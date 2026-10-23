from django.utils.html import format_html
from django.contrib import admin
from .models import (
    AnalysisJob,
    Document,
    DocumentChunk,
    Report,
    SimilarityResult,
    SourceJournal,
)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "uploaded_by",
        "file_type",
        "created_at",
    )

    list_display_links = ("id", "title")

    search_fields = (
        "title",
        "uploaded_by__username",
    )

    list_filter = (
        "file_type",
        "created_at",
    )

    ordering = ("-created_at",)

    list_per_page = 20

@admin.register(AnalysisJob)
class AnalysisJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "document",
        "colored_status",
        "similarity_index",
        "total_chunks",
        "matched_chunks",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "document__title",
    )

    ordering = ("-created_at",)

    list_per_page = 20

    list_select_related = ("document",)

    @admin.display(
        description="Status Analisis",
        ordering="status",
    )
    def colored_status(self, obj):
        colors = {
            "pending": "#64748B",
            "processing": "#D97706",
            "completed": "#15803D",
            "failed": "#DC2626",
        }

        color = colors.get(
            str(obj.status).lower(),
            "#64748B",
        )

        return format_html(
            '<span style="'
            'background-color: {};'
            'color: white;'
            'padding: 5px 12px;'
            'border-radius: 20px;'
            'font-weight: 600;'
            'display: inline-block;'
            '">'
            '{}'
            '</span>',
            color,
            obj.get_status_display(),
        )

admin.site.register(DocumentChunk)
admin.site.register(SourceJournal)
admin.site.register(SimilarityResult)
admin.site.register(Report)

# ==========================================
# IDENTITAS ADMIN ANTIKOPAS
# ==========================================

admin.site.site_header = "AntiKopas | Administrator"
admin.site.site_title = "AntiKopas Admin"
admin.site.index_title = "Dashboard Pengelolaan AntiKopas"