from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
def health(request):return JsonResponse({"status":"ok"})
def ready(request):
    try:
        connection.ensure_connection();cache.set("health-ready","ok",10)
        if cache.get("health-ready")!="ok":raise RuntimeError()
        return JsonResponse({"status":"ready"})
    except Exception:return JsonResponse({"status":"unavailable"},status=503)
