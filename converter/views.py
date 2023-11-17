from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .utils import dynamodb_to_json  

def is_valid_dynamodb_json(dynamodb_json):
    """ Validates if the input is structured as valid DynamoDB JSON. """
    def validate_attribute_value(attr_value):
        if isinstance(attr_value, dict) and len(attr_value) == 1:
            type_key = next(iter(attr_value))
            if type_key in ['S', 'N', 'BOOL', 'NULL']:
                return isinstance(attr_value[type_key], (str, bool, type(None)))
            elif type_key == 'M':
                return all(validate_attribute_value(v) for v in attr_value[type_key].values())
            elif type_key == 'L':
                return all(validate_attribute_value(item) for item in attr_value[type_key])
            else:
                return False
        return False

    if isinstance(dynamodb_json, dict):
        return all(
            validate_attribute_value(value)
            for value in dynamodb_json.values()
        )
    return False


@csrf_exempt
@require_http_methods(["POST"])
def convert_dynamodb_json(request):
    try:
        body_unicode = request.body.decode('utf-8')
        dynamodb_json = json.loads(body_unicode)
        
        if not is_valid_dynamodb_json(dynamodb_json):
            return HttpResponseBadRequest("Invalid DynamoDB JSON structure.")

        standard_json = dynamodb_to_json(dynamodb_json)
        return JsonResponse(standard_json, safe=False)
    except json.JSONDecodeError as e:
        return HttpResponseBadRequest(f"Invalid JSON format: {str(e)}")
    except ValueError as e:
        return HttpResponseBadRequest(f"Invalid DynamoDB JSON format: {str(e)}")
    except Exception as e:
        return HttpResponseBadRequest(f"An unexpected error occurred: {str(e)}")

def index(request):
    return render(request, 'converter/index.html')