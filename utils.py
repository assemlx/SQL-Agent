# utils.py
import re
import json

def extract_json_from_text(text: str):
    """
    Try to extract the first JSON object in the provided text.
    Returns the JSON string or None.
    """
    # Try to find a JSON object using braces
    start = text.find("{")
    if start == -1:
        return None
    # naive pairing braces -- find matching closing brace
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start:i+1]
                # validate JSON
                try:
                    json.loads(candidate)
                    return candidate
                except Exception:
                    return None
    return None
