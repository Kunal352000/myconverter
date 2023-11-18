from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .utils import dynamodb_to_json  

def dynamodb_to_json(dynamodb_json):
    """Recursively converts DynamoDB JSON format to standard JSON format."""
    if isinstance(dynamodb_json, list):
        return [dynamodb_to_json(item) for item in dynamodb_json]
    elif isinstance(dynamodb_json, dict):
        if 'M' in dynamodb_json:
            return {key: dynamodb_to_json(value) for key, value in dynamodb_json['M'].items()}
        elif 'L' in dynamodb_json:
            return [dynamodb_to_json(value) for value in dynamodb_json['L']]
        elif 'S' in dynamodb_json:
            return dynamodb_json['S']
        elif 'N' in dynamodb_json:
            return int(dynamodb_json['N']) if dynamodb_json['N'].isdigit() else float(dynamodb_json['N'])
        elif 'BOOL' in dynamodb_json:
            return dynamodb_json['BOOL']
        elif 'NULL' in dynamodb_json:
            return None
        else:
            return {key: dynamodb_to_json(value) for key, value in dynamodb_json.items()}
    else:
        return dynamodb_json

# The rest of your view function would remain the same.


def is_valid_dynamodb_json(dynamodb_json):
    """ Validates if the input is structured as valid DynamoDB JSON. """

    def is_valid_type_descriptor(key):
        return key in ['S', 'N', 'B', 'BOOL', 'NULL', 'M', 'L', 'SS', 'NS', 'BS']

    def validate_attribute_value(attr_value):
        if isinstance(attr_value, dict) and len(attr_value) == 1:
            type_key = next(iter(attr_value))
            if not is_valid_type_descriptor(type_key):
                return False

            value = attr_value[type_key]
            if type_key in ['S', 'N', 'B']:
                return isinstance(value, str)
            elif type_key == 'BOOL':
                return isinstance(value, bool)
            elif type_key == 'NULL':
                return value is True
            elif type_key == 'M':
                return isinstance(value, dict) and validate_map(value)
            elif type_key == 'L':
                return isinstance(value, list) and all(validate_attribute_value(elem) for elem in value)
            elif type_key in ['SS', 'NS', 'BS']:
                return isinstance(value, list) and all(isinstance(elem, str) for elem in value)
            else:
                return False
        else:
            return False

    def validate_map(attr_map):
        return all(validate_attribute_value(value) for value in attr_map.values())

    def validate_put_request(put_request):
        return 'Item' in put_request and validate_map(put_request['Item'])

    def validate_list_of_put_requests(list_of_put_requests):
        return all('PutRequest' in entry and validate_put_request(entry['PutRequest']) for entry in list_of_put_requests)

    if isinstance(dynamodb_json, dict):
        # It might be a simple key-value pair structure
        if all(isinstance(value, dict) for value in dynamodb_json.values()):
            return validate_map(dynamodb_json)
        else:
            for key, value in dynamodb_json.items():
                if isinstance(value, list):
                    if not validate_list_of_put_requests(value):
                        return False
                else:
                    return False
            return True

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