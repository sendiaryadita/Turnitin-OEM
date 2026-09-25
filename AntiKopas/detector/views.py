from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services.similarity import calculate_similarity


@api_view(["GET"])
def health_check(request):
    return Response({
        "status": "ok",
        "message": "AntiKopas API is running"
    })


@api_view(["GET", "POST"])
def detect_similarity(request):

    # =========================
    # GET
    # =========================
    if request.method == "GET":
        return Response({
            "status": "ok",
            "message": "AntiKopas Similarity Detection API",
            "method": "POST",
            "required_fields": [
                "title",
                "text",
                "comparison_text"
            ]
        })

    # =========================
    # POST
    # =========================

    title = request.data.get("title", "")
    text = request.data.get("text", "")
    comparison_text = request.data.get(
        "comparison_text",
        ""
    )

    if not text or not comparison_text:
        return Response({
            "status": "error",
            "message": "text dan comparison_text wajib diisi"
        }, status=400)

    try:

        score = calculate_similarity(
            text,
            comparison_text
        )

        return Response({
            "status": "success",
            "title": title,
            "similarity_score": score
        })

    except Exception as e:

        return Response({
            "status": "error",
            "message": str(e)
        }, status=500)