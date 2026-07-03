from datetime import timedelta
from decimal import Decimal

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from telegram import (
    LabeledPrice,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

from bot_app.models import (
    DiagnosticAnswer,
    DiagnosticQuestion,
    Lesson,
    Payment,
    Subscription,
    SubscriptionPlan,
    TelegramUser,
    UserLessonProgress,
    UserProfile,
)


# -------------------------
# Keyboards
# -------------------------

def diagnostic_keyboard():
    return ReplyKeyboardMarkup(
        [
            ['Начать диагностику'],
        ],
        resize_keyboard=True,
    )


def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ['Начать урок'],
            ['Мой прогресс', 'Слова'],
            ['Оформить подписку'],
            ['Условия подписки'],
        ],
        resize_keyboard=True,
    )


def paywall_keyboard():
    return ReplyKeyboardMarkup(
        [
            ['Оформить подписку'],
            ['Условия подписки'],
            ['Мой прогресс'],
        ],
        resize_keyboard=True,
    )



# -------------------------
# Helpers
# -------------------------

def normalize_answer(value: str) -> str:
    return (
        value
        .strip()
        .lower()
        .replace('.', '')
        .replace(',', '')
        .replace('?', '')
        .replace('!', '')
    )


@sync_to_async
def get_or_create_db_user(tg_user):
    user, _ = TelegramUser.objects.update_or_create(
        telegram_id=tg_user.id,
        defaults={
            'username': tg_user.username,
            'first_name': tg_user.first_name,
            'last_name': tg_user.last_name,
        }
    )

    profile, _ = UserProfile.objects.get_or_create(user=user)

    return {
        'id': user.id,
        'telegram_id': user.telegram_id,
        'first_name': user.first_name,
        'level': profile.level,
        'diagnostic_completed': profile.diagnostic_completed,
        'trial_lessons_used': profile.trial_lessons_used,
        'trial_lessons_limit': profile.trial_lessons_limit,
    }

@sync_to_async
def activate_mock_subscription(user_id: int):
    user = TelegramUser.objects.get(id=user_id)

    plan, _ = SubscriptionPlan.objects.get_or_create(
        code='monthly',
        defaults={
            'name': 'Месячный доступ',
            'price': Decimal('990.00'),
            'currency': 'RUB',
            'period': 'monthly',
            'is_active': True,
        }
    )

    amount = Decimal(settings.MONTHLY_SUBSCRIPTION_PRICE_KOPEKS) / Decimal('100')

    Payment.objects.create(
        user=user,
        provider='mock',
        status='succeeded',
        amount=amount,
        currency='RUB',
        payload=f'mock_monthly_subscription:{user.id}',
        raw_data={
            'mode': 'mock',
            'comment': 'Mock payment for development and YooKassa screenshots',
        },
    )

    now = timezone.now()

    current_subscription = Subscription.objects.filter(
        user=user,
        status='active',
        expires_at__gt=now,
    ).order_by('-expires_at').first()

    if current_subscription:
        start_date = current_subscription.expires_at
    else:
        start_date = now

    expires_at = start_date + timedelta(days=30)

    Subscription.objects.create(
        user=user,
        plan=plan,
        status='active',
        started_at=start_date,
        expires_at=expires_at,
    )

    return {
        'expires_at': expires_at,
    }


@sync_to_async
def get_user_by_telegram_id(telegram_id: int):
    user = TelegramUser.objects.get(telegram_id=telegram_id)
    profile = user.profile

    return {
        'id': user.id,
        'telegram_id': user.telegram_id,
        'first_name': user.first_name,
        'level': profile.level,
        'diagnostic_completed': profile.diagnostic_completed,
        'trial_lessons_used': profile.trial_lessons_used,
        'trial_lessons_limit': profile.trial_lessons_limit,
    }


@sync_to_async
def has_active_subscription(user_id: int) -> bool:
    return Subscription.objects.filter(
        user_id=user_id,
        status='active',
        expires_at__gt=timezone.now(),
    ).exists()


@sync_to_async
def get_next_diagnostic_question(user_id: int):
    answered_question_ids = DiagnosticAnswer.objects.filter(
        user_id=user_id
    ).values_list('question_id', flat=True)

    question = DiagnosticQuestion.objects.filter(
        is_active=True
    ).exclude(
        id__in=answered_question_ids
    ).order_by('order', 'id').first()

    if not question:
        return None

    return {
        'id': question.id,
        'text': question.text,
        'correct_answer': question.correct_answer,
        'order': question.order,
    }


@sync_to_async
def reset_diagnostic(user_id: int):
    DiagnosticAnswer.objects.filter(user_id=user_id).delete()

    profile = UserProfile.objects.get(user_id=user_id)
    profile.level = 'unknown'
    profile.diagnostic_completed = False
    profile.trial_lessons_used = 0
    profile.save(update_fields=[
        'level',
        'diagnostic_completed',
        'trial_lessons_used',
        'updated_at',
    ])


@sync_to_async
def save_diagnostic_answer_and_get_result(user_id: int, text: str):
    answered_question_ids = DiagnosticAnswer.objects.filter(
        user_id=user_id
    ).values_list('question_id', flat=True)

    question = DiagnosticQuestion.objects.filter(
        is_active=True
    ).exclude(
        id__in=answered_question_ids
    ).order_by('order', 'id').first()

    if not question:
        return {
            'status': 'already_completed',
        }

    user_normalized = normalize_answer(text)

    correct_variants = [
        normalize_answer(item)
        for item in question.correct_answer.split('|')
    ]

    is_correct = user_normalized in correct_variants

    DiagnosticAnswer.objects.create(
        user_id=user_id,
        question=question,
        user_answer=text,
        is_correct=is_correct,
    )

    remaining_question = DiagnosticQuestion.objects.filter(
        is_active=True
    ).exclude(
        id__in=DiagnosticAnswer.objects.filter(
            user_id=user_id
        ).values_list('question_id', flat=True)
    ).order_by('order', 'id').first()

    if remaining_question:
        return {
            'status': 'next_question',
            'is_correct': is_correct,
            'next_question': {
                'id': remaining_question.id,
                'text': remaining_question.text,
                'order': remaining_question.order,
            }
        }

    correct_count = DiagnosticAnswer.objects.filter(
        user_id=user_id,
        is_correct=True
    ).count()

    if correct_count <= 1:
        level = 'a1'
    elif correct_count == 2:
        level = 'a2'
    elif correct_count in [3, 4]:
        level = 'b1'
    else:
        level = 'b2'

    profile = UserProfile.objects.get(user_id=user_id)
    profile.level = level
    profile.diagnostic_completed = True
    profile.trial_lessons_used = 0
    profile.save(update_fields=[
        'level',
        'diagnostic_completed',
        'trial_lessons_used',
        'updated_at',
    ])

    return {
        'status': 'completed',
        'is_correct': is_correct,
        'correct_count': correct_count,
        'level': level,
    }


@sync_to_async
def get_progress_text(user_id: int):
    profile = UserProfile.objects.get(user_id=user_id)

    completed_lessons = UserLessonProgress.objects.filter(
        user_id=user_id,
        completed=True,
    ).count()

    active_subscription = Subscription.objects.filter(
        user_id=user_id,
        status='active',
        expires_at__gt=timezone.now(),
    ).order_by('-expires_at').first()

    if active_subscription:
        subscription_text = (
            f'Активна до: {active_subscription.expires_at.strftime("%d.%m.%Y")}'
        )
    else:
        subscription_text = 'Нет активной подписки'

    level = profile.level.upper() if profile.level != 'unknown' else 'не определён'

    return (
        'Твой прогресс:\n\n'
        f'Уровень: {level}\n'
        f'Пройдено уроков: {completed_lessons}\n'
        f'Пробных уроков использовано: '
        f'{profile.trial_lessons_used}/{profile.trial_lessons_limit}\n'
        f'Подписка: {subscription_text}'
    )


@sync_to_async
def get_next_lesson_for_user(user_id: int):
    profile = UserProfile.objects.get(user_id=user_id)

    if not profile.diagnostic_completed:
        return {
            'status': 'diagnostic_required',
        }

    active_subscription = Subscription.objects.filter(
        user_id=user_id,
        status='active',
        expires_at__gt=timezone.now(),
    ).exists()

    completed_lesson_ids = UserLessonProgress.objects.filter(
        user_id=user_id,
        completed=True,
    ).values_list('lesson_id', flat=True)

    lessons = Lesson.objects.filter(
        level=profile.level,
        is_active=True,
    ).exclude(
        id__in=completed_lesson_ids
    ).order_by('order', 'id')

    if not active_subscription:
        if profile.trial_lessons_used >= profile.trial_lessons_limit:
            return {
                'status': 'paywall',
            }

        lessons = lessons.filter(is_trial=True)

    lesson = lessons.first()

    if not lesson:
        if active_subscription:
            return {
                'status': 'no_lessons',
            }

        return {
            'status': 'paywall',
        }

    UserLessonProgress.objects.update_or_create(
        user_id=user_id,
        lesson=lesson,
        defaults={
            'completed': True,
            'completed_at': timezone.now(),
        }
    )

    if not active_subscription:
        profile.trial_lessons_used += 1
        profile.save(update_fields=[
            'trial_lessons_used',
            'updated_at',
        ])

    return {
        'status': 'lesson',
        'title': lesson.title,
        'content': lesson.content,
        'is_trial': lesson.is_trial,
        'trial_lessons_used': profile.trial_lessons_used,
        'trial_lessons_limit': profile.trial_lessons_limit,
        'active_subscription': active_subscription,
    }


@sync_to_async
def get_monthly_plan_data():
    plan, _ = SubscriptionPlan.objects.get_or_create(
        code='monthly',
        defaults={
            'name': 'Месячный доступ',
            'price': Decimal('990.00'),
            'currency': 'RUB',
            'period': 'monthly',
            'is_active': True,
        }
    )

    return {
        'id': plan.id,
        'code': plan.code,
        'name': plan.name,
        'price': plan.price,
        'currency': plan.currency,
    }


@sync_to_async
def validate_payment_payload(payload: str):
    if not payload.startswith('monthly_subscription:'):
        return False

    parts = payload.split(':')

    if len(parts) != 2:
        return False

    user_id = parts[1]

    return TelegramUser.objects.filter(id=user_id).exists()


@sync_to_async
def activate_subscription_after_payment(telegram_id: int, successful_payment):
    user = TelegramUser.objects.get(telegram_id=telegram_id)

    plan, _ = SubscriptionPlan.objects.get_or_create(
        code='monthly',
        defaults={
            'name': 'Месячный доступ',
            'price': Decimal('990.00'),
            'currency': 'RUB',
            'period': 'monthly',
            'is_active': True,
        }
    )

    amount = Decimal(successful_payment.total_amount) / Decimal('100')

    Payment.objects.create(
        user=user,
        provider='telegram_yookassa',
        status='succeeded',
        amount=amount,
        currency=successful_payment.currency,
        payload=successful_payment.invoice_payload,
        telegram_payment_charge_id=successful_payment.telegram_payment_charge_id,
        provider_payment_charge_id=successful_payment.provider_payment_charge_id,
        raw_data=successful_payment.to_dict(),
    )

    now = timezone.now()

    current_subscription = Subscription.objects.filter(
        user=user,
        status='active',
        expires_at__gt=now,
    ).order_by('-expires_at').first()

    if current_subscription:
        start_date = current_subscription.expires_at
    else:
        start_date = now

    expires_at = start_date + timedelta(days=30)

    Subscription.objects.create(
        user=user,
        plan=plan,
        status='active',
        started_at=start_date,
        expires_at=expires_at,
    )

    return {
        'expires_at': expires_at,
    }


# -------------------------
# Handlers
# -------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_user = await get_or_create_db_user(update.effective_user)

    name = db_user['first_name'] or 'друг'

    if not db_user['diagnostic_completed']:
        await update.message.reply_text(
            f'Привет, {name}! 👋\n\n'
            f'Я English Mentor Bot.\n\n'
            f'Сначала определим твой уровень английского. '
            f'Диагностика бесплатная и займёт пару минут.',
            reply_markup=diagnostic_keyboard(),
        )
        return

    active = await has_active_subscription(db_user['id'])

    if active:
        access_text = 'У тебя активная подписка.'
    elif db_user['trial_lessons_used'] < db_user['trial_lessons_limit']:
        access_text = (
            f'У тебя есть пробные уроки: '
            f'{db_user["trial_lessons_used"]}/{db_user["trial_lessons_limit"]}.'
        )
    else:
        access_text = 'Пробные уроки закончились. Для продолжения нужна подписка.'

    await update.message.reply_text(
        f'Привет, {name}! 👋\n\n'
        f'Твой уровень: {db_user["level"].upper()}.\n'
        f'{access_text}',
        reply_markup=main_keyboard() if active else paywall_keyboard(),
    )


async def start_diagnostic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_user = await get_or_create_db_user(update.effective_user)

    await reset_diagnostic(db_user['id'])

    question = await get_next_diagnostic_question(db_user['id'])

    if not question:
        await update.message.reply_text(
            'Пока нет вопросов для диагностики. Нужно добавить их в базу.'
        )
        return

    await update.message.reply_text(
        'Начинаем диагностику. Отвечай прямо сообщением.\n\n'
        f'Вопрос {question["order"]}:\n'
        f'{question["text"]}'
    )


async def handle_diagnostic_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_user = await get_or_create_db_user(update.effective_user)

    result = await save_diagnostic_answer_and_get_result(
        db_user['id'],
        update.message.text,
    )

    if result['status'] == 'next_question':
        await update.message.reply_text(
            f'Ответ принят.\n\n'
            f'Следующий вопрос {result["next_question"]["order"]}:\n'
            f'{result["next_question"]["text"]}'
        )
        return

    if result['status'] == 'completed':
        level = result['level'].upper()

        await update.message.reply_text(
            f'Диагностика завершена ✅\n\n'
            f'Твой уровень: {level}\n'
            f'Правильных ответов: {result["correct_count"]}\n\n'
            f'Теперь тебе доступны 2 пробных урока.',
            reply_markup=main_keyboard(),
        )
        return

    await update.message.reply_text(
        'Диагностика уже завершена.',
        reply_markup=main_keyboard(),
    )


async def start_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_user = await get_or_create_db_user(update.effective_user)

    lesson_data = await get_next_lesson_for_user(db_user['id'])

    if lesson_data['status'] == 'diagnostic_required':
        await update.message.reply_text(
            'Сначала нужно пройти бесплатную диагностику уровня.',
            reply_markup=diagnostic_keyboard(),
        )
        return

    if lesson_data['status'] == 'paywall':
        await update.message.reply_text(
            'Пробные уроки закончились 🔒\n\n'
            'Чтобы продолжить обучение, оформи месячный доступ.\n\n'
            'Что входит в подписку:\n'
            '— полный доступ к урокам;\n'
            '— прогресс;\n'
            '— слова;\n'
            '— дальнейшее развитие writing/speaking практики.',
            reply_markup=paywall_keyboard(),
        )
        return

    if lesson_data['status'] == 'no_lessons':
        await update.message.reply_text(
            'Для твоего уровня пока закончились уроки. Скоро добавим новые.',
            reply_markup=main_keyboard(),
        )
        return

    trial_note = ''

    if not lesson_data['active_subscription']:
        trial_note = (
            f'\n\nПробный урок использован: '
            f'{lesson_data["trial_lessons_used"]}/'
            f'{lesson_data["trial_lessons_limit"]}'
        )

    await update.message.reply_text(
        f'{lesson_data["content"]}'
        f'{trial_note}',
        reply_markup=main_keyboard(),
    )


async def show_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_user = await get_or_create_db_user(update.effective_user)
    text = await get_progress_text(db_user['id'])

    await update.message.reply_text(
        text,
        reply_markup=main_keyboard(),
    )


async def show_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_user = await get_or_create_db_user(update.effective_user)

    if not db_user['diagnostic_completed']:
        await update.message.reply_text(
            'Сначала нужно пройти диагностику.',
            reply_markup=diagnostic_keyboard(),
        )
        return

    await update.message.reply_text(
        'Твои слова:\n\n'
        'coffee — кофе\n'
        'tea — чай\n'
        'water — вода\n'
        'study — изучать\n'
        'practice — практика\n\n'
        'Позже здесь будут персональные слова из твоих уроков.',
        reply_markup=main_keyboard(),
    )


async def show_subscription_terms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Условия подписки English Mentor Bot:\n\n'
        'Стоимость: 990 ₽ за 30 дней доступа.\n\n'
        'Что входит:\n'
        '— полный доступ к урокам по твоему уровню;\n'
        '— отслеживание прогресса;\n'
        '— словарь изученных слов;\n'
        '— дальнейшие задания для практики английского.\n\n'
        'Бесплатно доступны:\n'
        '— диагностика уровня;\n'
        '— 2 пробных урока.\n\n'
        'После окончания оплаченного периода доступ к платным урокам закрывается. '
        'Для продолжения нужно оформить новый период доступа.\n\n'
        'Возврат и вопросы по оплате: напишите в поддержку проекта.',
        reply_markup=main_keyboard(),
    )


async def send_subscription_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_user = await get_or_create_db_user(update.effective_user)

    active = await has_active_subscription(db_user['id'])

    if active:
        await update.message.reply_text(
            'У тебя уже есть активная подписка ✅',
            reply_markup=main_keyboard(),
        )
        return

    if settings.PAYMENT_MODE == 'mock':
        result = await activate_mock_subscription(db_user['id'])

        await update.message.reply_text(
            'Тестовая оплата прошла успешно ✅\n\n'
            f'Подписка активирована до: {result["expires_at"].strftime("%d.%m.%Y")}.\n\n'
            'Это mock-режим для разработки и подготовки скриншотов для YooKassa.\n'
            'После одобрения магазина подключим реальную оплату.',
            reply_markup=main_keyboard(),
        )
        return

    if not settings.TELEGRAM_PAYMENT_PROVIDER_TOKEN:
        await update.message.reply_text(
            'Платежи пока не настроены: отсутствует TELEGRAM_PAYMENT_PROVIDER_TOKEN.'
        )
        return

    plan = await get_monthly_plan_data()

    payload = f'monthly_subscription:{db_user["id"]}'

    prices = [
        LabeledPrice(
            label=plan['name'],
            amount=settings.MONTHLY_SUBSCRIPTION_PRICE_KOPEKS,
        )
    ]

    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title='English Mentor Bot — месячный доступ',
        description=(
            'Полный доступ к урокам английского на 30 дней. '
            'После оплаты подписка активируется автоматически.'
        ),
        payload=payload,
        provider_token=settings.TELEGRAM_PAYMENT_PROVIDER_TOKEN,
        currency='RUB',
        prices=prices,
        start_parameter='english-mentor-monthly',
    )



async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query

    is_valid = await validate_payment_payload(query.invoice_payload)

    if not is_valid:
        await query.answer(
            ok=False,
            error_message='Ошибка платежа. Попробуй оформить подписку заново.'
        )
        return

    await query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    successful_payment = update.message.successful_payment

    result = await activate_subscription_after_payment(
        telegram_id=update.effective_user.id,
        successful_payment=successful_payment,
    )

    await update.message.reply_text(
        'Оплата прошла успешно ✅\n\n'
        f'Подписка активна до: {result["expires_at"].strftime("%d.%m.%Y")}.\n\n'
        'Теперь тебе доступен полный курс.',
        reply_markup=main_keyboard(),
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    db_user = await get_or_create_db_user(update.effective_user)

    if text == 'Начать диагностику':
        await start_diagnostic(update, context)
        return

    if not db_user['diagnostic_completed']:
        await handle_diagnostic_answer(update, context)
        return

    if text == 'Начать урок':
        await start_lesson(update, context)
        return

    if text == 'Мой прогресс':
        await show_progress(update, context)
        return

    if text == 'Слова':
        await show_words(update, context)
        return

    if text == 'Оформить подписку':
        await send_subscription_invoice(update, context)
        return
    
    if text == 'Условия подписки':
        await show_subscription_terms(update, context)
        return


    await update.message.reply_text(
        'Я пока понимаю команды из меню 👇',
        reply_markup=main_keyboard(),
    )


# -------------------------
# Django management command
# -------------------------

class Command(BaseCommand):
    help = 'Run Telegram bot'

    def handle(self, *args, **options):
        token = settings.TELEGRAM_BOT_TOKEN

        if not token:
            self.stdout.write(
                self.style.ERROR(
                    'TELEGRAM_BOT_TOKEN is empty. Add it to .env file.'
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS('Telegram bot is starting...')
        )

        application = ApplicationBuilder().token(token).build()

        application.add_handler(CommandHandler('start', start_command))

        application.add_handler(PreCheckoutQueryHandler(precheckout_callback))

        application.add_handler(
            MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback)
        )

        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
        )

        application.run_polling()
