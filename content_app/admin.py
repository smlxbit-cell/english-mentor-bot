from django.contrib import admin

from .models import (
    Character,
    ContentTheme,
    MediaAsset,
    Phrase,
    StoryArc,
    StoryEpisode,
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
    list_display = ('id', 'name', 'role', 'created_at')
    search_fields = ('name', 'role', 'personality')


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
