from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.functions import Coalesce
from django.utils import timezone


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


class AnalysisJobQuerySet(models.QuerySet):
    def with_expiration(self):
        finished = Coalesce("completed_at", "started_at", "created_at")
        active = Coalesce("started_at", "created_at")
        return self.annotate(
            _expires_at=models.Case(
                models.When(
                    status__in=["completed", "failed"],
                    then=finished + timedelta(hours=settings.ANALYSIS_RETENTION_HOURS),
                ),
                default=active + timedelta(hours=settings.ANALYSIS_STALE_HOURS),
                output_field=models.DateTimeField(),
            )
        )

    def active(self, at=None):
        return self.with_expiration().filter(_expires_at__gt=at or timezone.now())

    def expired(self, at=None):
        return self.with_expiration().filter(_expires_at__lte=at or timezone.now())


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

    # Progress pemeriksaan dokumen
    progress_percent = models.PositiveSmallIntegerField(
        default=0
    )

    progress_stage = models.CharField(
        max_length=100,
        default="Menunggu proses"
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

    objects = AnalysisJobQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Analysis #{self.pk} - {self.document.title}"

    # ==========================================
    # MASA SIMPAN HASIL ANALISIS: 2 JAM
    # ==========================================

    @property
    def expires_at(self):
        """
        Hasil selesai/gagal: sejak selesai (fallback mulai/dibuat).
        Pending/processing: batas proses dihitung sejak mulai/dibuat.
        """
        if self.status in {self.Status.COMPLETED, self.Status.FAILED}:
            anchor = self.completed_at or self.started_at or self.created_at
            hours = settings.ANALYSIS_RETENTION_HOURS
        else:
            anchor = self.started_at or self.created_at
            hours = settings.ANALYSIS_STALE_HOURS
        return anchor + timedelta(hours=hours) if anchor else None

    @property
    def is_expired(self):
        """
        Memeriksa apakah masa simpan sudah berakhir.
        """
        expiration = self.expires_at

        if expiration is None:
            return False

        return timezone.now() >= expiration


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
