from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from .utils import dynamodb_to_json  # Assuming the conversion function is in utils.py

@csrf_exempt
@require_http_methods(["POST"])
def convert_dynamodb_json(request):
    try:
        dynamodb_json = json.loads(request.body)
        standard_json = dynamodb_to_json(dynamodb_json)
        return JsonResponse(standard_json, safe=False)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON format")

    except Exception as e:
        return HttpResponseBadRequest(f"Error during conversion: {str(e)}")

def index(request):
    return render(request, 'converter/index.html')