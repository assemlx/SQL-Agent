# db.py
import mysql.connector
from mysql.connector import errorcode


class MySQLDB:
    def __init__(self, config: dict):
        self.host = config["host"]
        self.port = config.get("port", 3306)
        self.user = config["user"]
        self.password = config["password"]
        self.database = config.get("database")  # may be None initially
        self._conn = None

    def connect(self):
        """
        Connect to MySQL. If database is not set yet, connect only to server.
        """
        if self._conn:
            return self._conn

        conn_config = {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "autocommit": False,
        }

        if self.database:  # only add db if user selected it
            conn_config["database"] = self.database

        self._conn = mysql.connector.connect(**conn_config)
        return self._conn

    def reconnect_with_db(self, db_name):
        """Recreate connection using selected database."""
        self.close()
        self.database = db_name
        return self.connect()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ----------------------------------------------------
    # NEW: list all databases from MySQL server
    # ----------------------------------------------------
    def list_databases(self):
        """
        Return a list of database names available on the server.
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES;")
        dbs = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return dbs

    # ----------------------------------------------------
    # NEW: set database after user selects one
    # ----------------------------------------------------
    def set_database(self, db_name):
        """
        Change the active database by reconnecting.
        """
        self.reconnect_with_db(db_name)

    # ----------------------------------------------------
    # Load schema summary from selected DB
    # ----------------------------------------------------
    def get_schema_summary(self):
        """
        Return a compact text summary of tables and columns.
        Only works if a database is selected.
        """
        if not self.database:
            return "No database selected."

        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME, ORDINAL_POSITION;
        """, (self.database,))
        rows = cursor.fetchall()
        cursor.close()

        schema = {}
        for table, col, ctype in rows:
            schema.setdefault(table, []).append(f"{col} {ctype}")

        parts = []
        for t, cols in schema.items():
            parts.append(f"{t}({', '.join(cols)})")

        return "\n".join(parts)

    # ----------------------------------------------------
    # SQL execution
    # ----------------------------------------------------
    def execute_select(self, query, params):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        cursor.close()
        return rows, columns

    def execute_dml(self, query, params):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        affected = cursor.rowcount
        conn.commit()
        cursor.close()
        return affected
