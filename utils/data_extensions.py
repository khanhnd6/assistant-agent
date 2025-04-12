import json

def remove_first_underscore(obj):
    if isinstance(obj, dict):
        return {
            key.replace('_', '', 1): remove_first_underscore(value)
            for key, value in obj.items()
        }
    elif isinstance(obj, list):
        return [remove_first_underscore(item) for item in obj]
    else:
        return obj

def remove_empty_values(data, remove_zero=False, return_as_string=False):
    """
    Removes keys with empty values from a dict, list of dicts, or JSON string.
    Empty values: None, '', [], {}, and 0 (if remove_zero=True).
    """
    def is_empty(value):
        return (
            value is None or value == '' or value == [] or value == {} or
            (remove_zero and value == 0)
        )

    def clean_dict(d):
        return {k: v for k, v in d.items() if not is_empty(v)}

    # Parse JSON string if needed
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON string input")

    # Handle list of dicts
    if isinstance(data, list):
        cleaned = [clean_dict(item) for item in data if isinstance(item, dict)]
    elif isinstance(data, dict):
        cleaned = clean_dict(data)
    else:
        raise TypeError("Input must be a dict, list of dicts, or valid JSON string")

    return json.dumps(cleaned, indent=2) if return_as_string else cleaned
