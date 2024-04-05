from django.contrib import admin, messages

from .models import Newsletter, Paper, PaperTopic
from newsletter.utils.send_newsletters import send_email_newsletter
from mptt.admin import MPTTModelAdmin


class NewsletterAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ["title"]}
    date_hierarchy = 'created_at'
    list_display = (
        'title', 'topic', 'schedule', 'sent_at',
    )
    search_fields = ('topic', 'title')
    readonly_fields = ('created_at', 'sent_at',)
    sortable_by = ('schedule', 'sent_at', 'created_at')

    actions = ('send_newsletters',)

    def send_newsletters(self, request, queryset):
        # This should always be overridden to use a task
        send_email_newsletter(newsletters=queryset, respect_schedule=False)
        messages.add_message(
            request,
            messages.SUCCESS,
            'Sending selected newsletters(s) to the subscribers',
        )

    send_newsletters.short_description = 'Send newsletters'


class PaperAdmin(admin.ModelAdmin):
    list_select_related = ('topic',)
    list_display = (
        'title', 'topic',
        'source_url', 'is_visible',
    )
    list_filter = ('is_visible', 'topic', 'published_at')
    search_fields = (
        'title', 'abstract',
        'topic__title',
    )
    readonly_fields = ('created_at', 'updated_at',)
    autocomplete_fields = ('topic',)

    actions = ('hide_post', 'make_post_visible',)

    def hide_post(self, request, queryset):
        updated = queryset.update(is_visible=False)
        messages.add_message(
            request,
            messages.SUCCESS,
            f'Successfully marked {updated} post(s) as hidden',
        )

    hide_post.short_description = 'Hide posts from users'

    def make_post_visible(self, request, queryset):
        updated = queryset.update(is_visible=True)
        messages.add_message(
            request,
            messages.SUCCESS,
            f'Successfully made {updated} post(s) visible',
        )

    make_post_visible.short_description = 'Make posts visible'


class CustomMPTTModelAdmin(MPTTModelAdmin):
    mptt_level_indent = 20


admin.site.register(Newsletter, NewsletterAdmin)
admin.site.register(Paper)
admin.site.register(PaperTopic, CustomMPTTModelAdmin)
