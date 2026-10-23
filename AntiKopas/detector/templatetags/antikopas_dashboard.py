from datetime import timedelta

from django import template
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from detector.models import AnalysisJob, Document


register = template.Library()


@register.simple_tag
def antikopas_dashboard_data():
    """
    Menyediakan statistik database untuk Django Admin.
    """

    User = get_user_model()

    # ==========================================
    # 1. STATISTIK UTAMA
    # ==========================================

    total_users = User.objects.count()
    total_documents = Document.objects.count()
    total_analyses = AnalysisJob.objects.count()

    completed_analyses = AnalysisJob.objects.filter(
        status=AnalysisJob.Status.COMPLETED
    ).count()

    failed_analyses = AnalysisJob.objects.filter(
        status=AnalysisJob.Status.FAILED
    ).count()

    processing_analyses = AnalysisJob.objects.filter(
        status__in=[
            AnalysisJob.Status.PENDING,
            AnalysisJob.Status.PROCESSING,
        ]
    ).count()

    # ==========================================
    # 2. GRAFIK AKTIVITAS 30 HARI
    # ==========================================

    today = timezone.localdate()
    start_date = today - timedelta(days=29)

    daily_results = (
        AnalysisJob.objects
        .filter(
            created_at__date__gte=start_date,
            created_at__date__lte=today,
        )
        .order_by()
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(
            completed=Count(
                "id",
                filter=Q(
                    status=AnalysisJob.Status.COMPLETED
                ),
            ),
            failed=Count(
                "id",
                filter=Q(
                    status=AnalysisJob.Status.FAILED
                ),
            ),
        )
    )

    daily_lookup = {
        item["day"]: item
        for item in daily_results
    }

    max_daily = max(
        [
            max(
                item["completed"],
                item["failed"],
            )
            for item in daily_lookup.values()
        ] + [1]
    )

    chart = []
    line_points = []

    for index in range(30):
        day = start_date + timedelta(days=index)

        values = daily_lookup.get(day, {})

        completed = values.get("completed", 0)
        failed = values.get("failed", 0)

        completed_height = round(
            completed / max_daily * 140,
            2
        )

        failed_height = round(
            failed / max_daily * 140,
            2
        )

        x = 16 + index * 23

        chart.append({
            "date": day,
            "completed": completed,
            "failed": failed,
            "x": x,
            "failed_x": x + 8,
            "completed_y": 180 - completed_height,
            "failed_y": 180 - failed_height,
            "completed_height": completed_height,
            "failed_height": failed_height,
            "label_x": x + 4,
            "label": (
                day.strftime("%d %b")
                if index % 5 == 0 or index == 29
                else ""
            ),
        })

        line_points.append(
            f"{x + 3},{180 - completed_height:.2f}"
        )

    # ==========================================
    # 3. UKURAN DOKUMEN
    # ==========================================

    total_file_size = (
        Document.objects.aggregate(
            total=Sum("file_size")
        )["total"] or 0
    )

    document_size_mb = round(
        total_file_size / (1024 * 1024),
        2
    )

    # ==========================================
    # 4. ANALISIS TERBARU
    # ==========================================

    recent_analyses = (
        AnalysisJob.objects
        .select_related(
            "document",
            "document__uploaded_by",
        )
        .order_by("-created_at")[:5]
    )

    # ==========================================
    # 5. DATA DASHBOARD
    # ==========================================

    return {
        "total_users": total_users,
        "total_documents": total_documents,
        "total_analyses": total_analyses,
        "completed_analyses": completed_analyses,
        "failed_analyses": failed_analyses,
        "processing_analyses": processing_analyses,
        "document_size_mb": document_size_mb,
        "recent_analyses": recent_analyses,
        "chart": chart,
        "line_points": " ".join(line_points),
    }