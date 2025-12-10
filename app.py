# app.py
import os
import json
import chainlit as cl
from chainlit.input_widget import TextInput, Select
from google import genai
from dotenv import load_dotenv

from agent import NLToSQLAgent
from db import MySQLDB
from safety import is_query_safe

load_dotenv()

# Gemini client
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise RuntimeError("Please set GEMINI_API_KEY")

client = genai.Client(api_key=gemini_api_key)
MODEL_ID = "gemini-2.5-flash"

agent = NLToSQLAgent(client=client, model=MODEL_ID)


# ---------------------------------------------------------
# CHAT START — ASK FOR SERVER CONFIG (NO DB NAME)
# ---------------------------------------------------------
@cl.on_chat_start
async def start():
    inputs = await cl.ChatSettings(
        [
            TextInput(id="db_host", label="DB Host", initial=os.getenv("DB_HOST")),
            TextInput(id="db_port", label="DB Port", initial=os.getenv("DB_PORT")),
            TextInput(id="db_user", label="DB Username", initial=os.getenv("DB_USER")),
            TextInput(id="db_password", label="DB Password", initial=os.getenv("DB_PASSWORD")),
        ]
    ).send()

    # Save server login (without DB name yet)
    cl.user_session.set("server_login", inputs)

    # Connect using provided credentials to fetch db list
    temp_db = MySQLDB({
        "host": inputs["db_host"],
        "port": int(inputs["db_port"]),
        "user": inputs["db_user"],
        "password": inputs["db_password"],
        "database": None
    })

    try:
        db_list = temp_db.list_databases()
    except Exception as e:
        await cl.Message(content=f"Cannot connect: {e}").send()
        return

    # Ask user to select DB
    await cl.Message(
        content="Choose database:",
        actions=[
            cl.Action(
                name="select_db",
                label=db,
                payload={"db": db}
            )
            for db in db_list
        ]
    ).send()


    # Mark that we are waiting for DB selection
    cl.user_session.set("awaiting_db", True)


# ---------------------------------------------------------
# ACTION HANDLER — USER SELECTS DATABASE
# ---------------------------------------------------------
@cl.action_callback("select_db")
async def on_db_select(action):
    server_login = cl.user_session.get("server_login")

    # Extract selected DB
    selected_db = action.payload["db"]

    final_config = {
        "host": server_login["db_host"],
        "port": int(server_login["db_port"]),
        "user": server_login["db_user"],
        "password": server_login["db_password"],
        "database": selected_db,
        "allow_dml": True,
    }

    cl.user_session.set("db_config", final_config)
    cl.user_session.set("awaiting_db", False)

    await cl.Message(
        content=f"Connected to database **{selected_db}**.\n\nYou can now ask your SQL questions!"
    ).send()



# ---------------------------------------------------------
# MAIN CHAT MESSAGE HANDLER
# ---------------------------------------------------------
@cl.on_message
async def main(message: cl.Message):
    # Wait until DB selection finished
    if cl.user_session.get("awaiting_db", False):
        await cl.Message(content="Please select a database first.").send()
        return

    db_config = cl.user_session.get("db_config")
    if not db_config:
        await cl.Message(content="No DB configuration found. Restart the chat.").send()
        return

    # Create DB object
    db = MySQLDB(db_config)
    schema = db.get_schema_summary()

    try:
        result = agent.nl_to_sql(
            user_nl=message.content,
            schema=schema,
            allow_dml=db_config["allow_dml"],
        )
    except Exception as e:
        await cl.Message(content=f"Error generating SQL: {e}").send()
        return

    query = result.get("query")
    params = result.get("params", [])
    explain = result.get("explain", "")
    qtype = result.get("type", "")

    if not query:
        await cl.Message(content="No SQL was generated. Try rewriting your question.").send()
        return

    if not is_query_safe(query, allow_dml=db_config["allow_dml"]):
        await cl.Message(content="Unsafe SQL detected. Refusing to execute.").send()
        return

    try:
        if qtype == "SELECT":
            rows, cols = db.execute_select(query, params)
            preview = rows[:10]
            md = format_table_md(cols, preview)

            await cl.Message(
                content=f"```sql\n{query}\n```\n**Params:** {params}\n\n**Explanation:** {explain}\n\n{md}"
            ).send()

        else:
            affected = db.execute_dml(query, params)
            await cl.Message(
                content=f"```sql\n{query}\n```\n**Params:** {params}\n\n**Affected rows:** {affected}"
            ).send()

    except Exception as e:
        await cl.Message(content=f"Execution error: {e}").send()


def format_table_md(columns, rows):
    if not columns:
        return "No results."

    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = "\n".join(
        "| " + " | ".join([str(c) for c in r]) + " |" for r in rows
    )
    return "\n".join([header, sep, body])