"""LEGACY app — intentionally not registered in admin.

The live bot writes users to `users_app.UserProfile` (see telegram_app.bot.db).
`bot_app`'s TelegramUser/UserProfile/Subscription/Lesson models are retained
only for their historical migrations and must NOT be used for new data. Look
for real (test) users under Users_app > User profiles.
"""

# Deliberately empty: do not register bot_app models.
