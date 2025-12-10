# agent.py
import json
import re
import time
from google import genai
from google.genai import types
from utils import extract_json_from_text

class NLToSQLAgent:
    """
    Turns natural language into a parameterized SQL statement + params list using Gemini.
    The model is asked to return a JSON object, e.g.:
    {
      "query": "SELECT name, age FROM users WHERE country = %s AND created_at > %s",
      "params": ["Egypt", "2025-01-01"],
      "explain": "Selecting user names and ages for users in Egypt created after 2025-01-01",
      "type": "SELECT"
    }
    """
    RETRY_MAX = 5
    RETRY_BASE_SEC = 1.5  # exponential backoff starting at 1.5 seconds

    PROMPT_TEMPLATE = """
You are an expert SQL generator. Given the DB schema and a user request, produce a parameterized SQL statement using placeholders %s
and a JSON response (ONLY JSON) with keys: query, params, explain, type.
Schema:
{schema}

User request:
{nl}

Rules:
1) Use parameter placeholders `%s` (the MySQL parameter style).
2) Return EXACTLY one JSON object. Do not include any commentary outside the JSON.
3) For SELECT queries, return type = "SELECT". For insert/update/delete return "INSERT"/"UPDATE"/"DELETE".
4) If the request is ambiguous, try to choose a safe behavior (e.g. ask for clarification) by returning an "explain" that requests clarification and a query of null.
5) Do NOT interpolate user input into the SQL; instead, put values into "params".
6) If the user asks to modify data (INSERT/UPDATE/DELETE) and allow_dml is False, return a JSON with query:null and explain stating DML not allowed.

Produce the JSON now.
"""

    def __init__(self, client: genai.Client, model="gemini-2.5-flash"):
        self.client = client
        self.model = model

    def _call_model_with_retry(self, prompt_text):
        last_error = None
        for attempt in range(self.RETRY_MAX):
            try:
                return self.client.models.generate_content(
                    model=self.model,
                    contents=prompt_text,
                )
            except Exception as e:
                last_error = e
                # If it's a 503 overloaded error, retry
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    sleep_time = self.RETRY_BASE_SEC * (2 ** attempt)
                    time.sleep(sleep_time)
                    continue
                else:
                    raise e  # Unknown error → do not retry
        raise RuntimeError(f"Model overloaded after {self.RETRY_MAX} retries. Last error: {last_error}")

    def nl_to_sql(self, user_nl: str, schema: str, allow_dml: bool = False):
        prompt = self.PROMPT_TEMPLATE.format(schema=schema, nl=user_nl)

        # Use retry wrapper
        response = self._call_model_with_retry(prompt)

        text = response.text or ""
        jtext = extract_json_from_text(text)
        if jtext is None:
            raise ValueError("Could not parse JSON from model response:\n" + text)

        data = json.loads(jtext)

        typ = data.get("type", "").upper()
        if typ in ["INSERT", "UPDATE", "DELETE"] and not allow_dml:
            return {
                "query": None,
                "params": [],
                "explain": "DML detected but disallowed by session settings.",
                "type": typ,
            }

        return data
