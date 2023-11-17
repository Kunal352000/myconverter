def dynamodb_to_json(dynamodb_json):
    """ Convert DynamoDB JSON to standard JSON. """
    def parse(obj):
        if isinstance(obj, dict):
            if 'S' in obj:
                return obj['S']
            elif 'N' in obj:
                return int(obj['N']) if obj['N'].isdigit() else float(obj['N'])
            elif 'BOOL' in obj:
                return obj['BOOL']
            elif 'NULL' in obj:
                return None
            elif 'M' in obj:
                return {k: parse(v) for k, v in obj['M'].items()}
            elif 'L' in obj:
                return [parse(item) for item in obj['L']]
            else:
                return {k: parse(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [parse(item) for item in obj]
        else:
            return obj

    return parse(dynamodb_json)
