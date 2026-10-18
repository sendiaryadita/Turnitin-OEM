from django.contrib import admin
from .models import (
    AnalysisJob,
    Document,
    DocumentChunk,
    Report,
    SimilarityResult,
    SourceJournal,
)

admin.site.register(Document)
admin.site.register(AnalysisJob)
admin.site.register(DocumentChunk)
admin.site.register(SourceJournal)
admin.site.register(SimilarityResult)
admin.site.register(Report)
