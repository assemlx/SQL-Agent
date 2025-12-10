# safety.py
import re

ALLOWED_SELECT = True
ALLOWED_DML = False

def detect_sql_type(sql: str):
    if not sql:
        return "UNKNOWN"
    s = sql.strip().lower()
    if s.startswith("select"):
        return "SELECT"
    if s.startswith("insert"):
        return "INSERT"
    if s.startswith("update"):
        return "UPDATE"
    if s.startswith("delete"):
        return "DELETE"
    return "OTHER"

def is_query_safe(query: str, allow_dml: bool = False):
    """
    Basic checks:
    - disallow multiple statements separated by ';' (so no stacked queries)
    - only allow expected statement types
    - disallow dangerous keywords like 'drop', 'truncate', 'alter'
    """
    if not query:
        return False
    if ";" in query.strip().rstrip(";"):
        # stacked queries — refuse
        return False
    q_lower = query.lower()
    for bad in ["drop ", "truncate ", "alter ", "shutdown ", "create "]:
        if bad in q_lower:
            return False
    typ = detect_sql_type(query)
    if typ in ["INSERT", "UPDATE", "DELETE"]:
        return allow_dml
    if typ == "SELECT":
        return True
    # conservative default
    return False
