import random

from django.shortcuts import get_object_or_404, redirect, render

from .forms import WordForm
from .models import Word


def word_list(request):
    words = Word.objects.all()

    return render(
        request,
        'learning/word_list.html',
        {
            'words': words,
        }
    )


def word_create(request):
    if request.method == 'POST':
        form = WordForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('learning:word_list')
    else:
        form = WordForm()

    return render(
        request,
        'learning/word_form.html',
        {
            'form': form,
        }
    )


def get_answer_options(word):
    wrong_answers = list(
        Word.objects
        .exclude(id=word.id)
        .values_list('translation', flat=True)
        .order_by('?')[:3]
    )

    options = [word.translation] + wrong_answers
    random.shuffle(options)

    return options


def word_training(request):
    result = None
    word = None
    options = []
    selected_answer = ''

    if request.method == 'POST':
        word_id = request.POST.get('word_id')
        selected_answer = request.POST.get('answer', '')

        word = get_object_or_404(Word, id=word_id)

        is_correct = selected_answer == word.translation

        result = {
            'is_correct': is_correct,
            'correct_answer': word.translation,
            'selected_answer': selected_answer,
        }
    else:
        word = Word.objects.order_by('?').first()

        if word:
            options = get_answer_options(word)

    return render(
        request,
        'learning/training.html',
        {
            'word': word,
            'options': options,
            'result': result,
        }
    )
