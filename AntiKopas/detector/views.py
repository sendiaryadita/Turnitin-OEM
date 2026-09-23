from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .services.similarity import calculate_similarity


def health_check(request):
    return JsonResponse({
        "status": "ok",
        "message": "AntiKopas API is running"
    })


@csrf_exempt
def detect_similarity(request):

    if request.method != "POST":
        return JsonResponse({
            "status": "error",
            "message": "Only POST method is allowed"
        }, status=405)

    try:
        data = json.loads(request.body)

        title = data.get("title", "")
        text = data.get("text", "")
        comparison_text = data.get("comparison_text", "")

        if not text or not comparison_text:
            return JsonResponse({
                "status": "error",
                "message": "text dan comparison_text wajib diisi"
            }, status=400)

        score = calculate_similarity(
            text,
            comparison_text
        )

        return JsonResponse({
            "status": "success",
            "title": title,
            "similarity_score": score
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)