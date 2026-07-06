from django.contrib import admin

from .models import (
    Character,
    CharacterMedia,
    ContentTheme,
    DiagnosticItem,
    GrammarRule,
    Lesson,
    LessonStep,
    MediaAsset,
    Phrase,
    StoryArc,
    StoryEpisode,
    Unit,
)


@admin.register(ContentTheme)
class ContentThemeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Phrase)
class PhraseAdmin(admin.ModelAdmin):
    list_display = ('id', 'english_text', 'translation', 'level', 'theme', 'created_at')
    list_filter = ('level', 'theme', 'created_at')
    search_fields = ('english_text', 'translation', 'explanation')


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'role', 'has_video_note', 'created_at')
    search_fields = ('name', 'role', 'personality')
    fields = (
        'name', 'role', 'personality', 'speaking_style',
        'avatar_url', 'video_note_file_id',
    )

    @admin.display(boolean=True, description='Video')
    def has_video_note(self, obj):
        return bool(obj.video_note_file_id)


class CharacterMediaInline(admin.TabularInline):
    model = CharacterMedia
    extra = 0
    fields = ('key', 'kind', 'title', 'source_path', 'telegram_file_id')


CharacterAdmin.inlines = [CharacterMediaInline]


@admin.register(CharacterMedia)
class CharacterMediaAdmin(admin.ModelAdmin):
    list_display = ('character', 'key', 'kind', 'title', 'has_file_id')
    list_filter = ('kind', 'character')
    search_fields = ('key', 'title', 'character__name')

    @admin.display(boolean=True, description='TG')
    def has_file_id(self, obj):
        return bool(obj.telegram_file_id)


class StoryEpisodeInline(admin.TabularInline):
    model = StoryEpisode
    extra = 0
    fields = ('episode_number', 'title', 'level', 'theme', 'is_published')
    show_change_link = True


@admin.register(StoryArc)
class StoryArcAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'slug', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [StoryEpisodeInline]


@admin.register(StoryEpisode)
class StoryEpisodeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'arc',
        'episode_number',
        'title',
        'level',
        'theme',
        'is_published',
        'created_at',
    )
    list_filter = ('level', 'theme', 'is_published', 'created_at')
    search_fields = ('title', 'short_summary', 'story_text')
    filter_horizontal = ('characters', 'target_phrases')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ('id', 'media_type', 'title', 'source_url', 'created_at')
    list_filter = ('media_type', 'created_at')
    search_fields = ('title', 'source_url', 'author')


@admin.register(DiagnosticItem)
class DiagnosticItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'level', 'skill', 'item_type', 'order', 'is_active')
    list_filter = ('level', 'skill', 'item_type', 'is_active')
    search_fields = ('prompt',)
    ordering = ('level', 'order')


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ('order', 'title', 'level', 'is_trial', 'is_published', 'xp_reward')
    show_change_link = True
    ordering = ('order',)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'level', 'order', 'is_published', 'created_at')
    list_filter = ('level', 'is_published')
    search_fields = ('title', 'slug', 'description')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('level', 'order')
    inlines = [LessonInline]


class LessonStepInline(admin.TabularInline):
    model = LessonStep
    extra = 0
    fields = ('order', 'step_type', 'skill', 'title', 'xp_reward', 'is_optional')
    show_change_link = True
    ordering = ('order',)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'title', 'unit', 'level', 'order', 'is_trial', 'is_published',
        'xp_reward', 'estimated_minutes',
    )
    list_filter = ('level', 'is_trial', 'is_published', 'unit', 'theme')
    search_fields = ('title', 'subtitle')
    ordering = ('level', 'order')
    inlines = [LessonStepInline]


@admin.register(LessonStep)
class LessonStepAdmin(admin.ModelAdmin):
    list_display = ('id', 'lesson', 'order', 'step_type', 'skill', 'title')
    list_filter = ('step_type', 'skill')
    search_fields = ('title', 'text')
    ordering = ('lesson', 'order')


@admin.register(GrammarRule)
class GrammarRuleAdmin(admin.ModelAdmin):
    list_display = ('id', 'key', 'title', 'topic', 'level', 'order', 'is_published')
    list_filter = ('level', 'topic', 'is_published')
    search_fields = ('key', 'title', 'topic', 'summary_ru')
    ordering = ('level', 'topic', 'order')
