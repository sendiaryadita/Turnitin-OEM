from django.contrib.auth.models import User
from django.db import models


class Document(models.Model):
    """Dokumen akademik yang dikirim untuk dianalisis."""

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    title = models.CharField(max_length=500)
    original_file = models.FileField(
        upload_to="documents/%Y/%m/"
    )
    file_type = models.CharField(max_length=20, blank=True)
    file_size = models.PositiveBigIntegerField(default=0)
    sha256 = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class AnalysisJob(models.Model):
    """Satu proses analisis terhadap sebuah dokumen."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="analyses",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    total_chunks = models.PositiveIntegerField(default=0)
    matched_chunks = models.PositiveIntegerField(default=0)
    similarity_index = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Analysis #{self.pk} - {self.document.title}"


class DocumentChunk(models.Model):
    """Potongan teks dokumen yang dianalisis."""

    analysis = models.ForeignKey(
        AnalysisJob,
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    chunk_index = models.PositiveIntegerField()
    text = models.TextField()
    token_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["chunk_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["analysis", "chunk_index"],
                name="unique_analysis_chunk_index",
            )
        ]

    def __str__(self):
        return f"Chunk {self.chunk_index} - Analysis #{self.analysis_id}"


class SourceJournal(models.Model):
    """Metadata sumber akademik yang ditemukan dari OpenAlex."""

    openalex_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
    )
    title = models.CharField(max_length=1000)
    year = models.PositiveIntegerField(null=True, blank=True)
    doi = models.CharField(max_length=500, blank=True, db_index=True)
    url = models.URLField(max_length=2000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class SimilarityResult(models.Model):
    """Hasil perbandingan satu chunk dengan satu sumber akademik."""

    analysis = models.ForeignKey(
        AnalysisJob,
        on_delete=models.CASCADE,
        related_name="similarity_results",
    )
    chunk = models.ForeignKey(
        DocumentChunk,
        on_delete=models.CASCADE,
        related_name="similarity_results",
    )
    source = models.ForeignKey(
        SourceJournal,
        on_delete=models.CASCADE,
        related_name="similarity_results",
    )
    embedding_score = models.FloatField(null=True, blank=True)
    cross_encoder_score = models.FloatField(null=True, blank=True)
    matched = models.BooleanField(default=False, db_index=True)
    validation_reason = models.CharField(max_length=255, blank=True)
    source_excerpt = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["analysis", "chunk", "source"],
                name="unique_similarity_result",
            )
        ]


class Report(models.Model):
    """File laporan PDF untuk sebuah proses analisis."""

    analysis = models.OneToOneField(
        AnalysisJob,
        on_delete=models.CASCADE,
        related_name="report",
    )
    file = models.FileField(upload_to="reports/%Y/%m/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report #{self.pk} - Analysis #{self.analysis_id}"
