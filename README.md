🚀 SQL Agent with Gemini + Chainlit

A fully interactive SQL Agent that connects to your MySQL Server, executes SQL queries safely, and lets you chat naturally with an AI assistant powered by Google Gemini — all inside a Chainlit UI.

🌟 Features

🔐 Secure MySQL connection from user-provided configuration

🤖 AI-powered SQL generation using Google Gemini

🛠️ Real SQL execution on your MySQL server

📝 Automatic query explanation

🧠 Memory & Context: The agent understands your database structure

💬 Beautiful Chainlit chat UI

⚠️ Safety filters to prevent destructive queries unless confirmed

📂 Project Structure
SQL-Agent/
│
├── app.py                    # Chainlit UI entry point
├── agent/
│   ├── sql_agent.py          # Gemini agent + SQL execution logic
│   ├── db.py                 # MySQL connection wrapper
│   └── prompts.py            # System prompts for the agent
│
├── config/
│   └── config_schema.json    # Validation schema for connection inputs
│
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation

🧰 Requirements

Install dependencies:

pip install -r requirements.txt


You need:

✔ Python 3.10+
✔ MySQL running locally or remotely
✔ Google Gemini API Key
✔ Chainlit installed

🔧 Configuration Inputs

When the app starts, Chainlit will ask for:

MySQL host

MySQL port

Username

Password

Database name

Gemini API key

After entering them, the agent initializes and starts the chat.

▶️ How to Run

Clone the repo:

git clone https://github.com/assemlx/SQL-Agent.git
cd SQL-Agent


Install dependencies:

pip install -r requirements.txt


Run the Chainlit app:

chainlit run app.py -w


Open the UI from:

http://localhost:8000

💡 Usage

You can ask the agent:

“Show me all users created last week.”
“Add a column ‘status’ to orders.”
“Fix this SQL error…”
“Explain the following query…”
“Insert a new product into the table.”

The agent will:

Generate SQL using Gemini

Run it on your MySQL server

Show the result nicely in chat

Explain what happened

🛡️ Safety

The agent prevents harmful actions unless explicitly approved:

DROP DATABASE

DROP TABLE

TRUNCATE

Mass deletion without WHERE clause

It will ask:

“This operation is dangerous. Do you want to continue? (yes/no)”

📦 Deployment (Optional)

Deploy options:

Docker

Streamlit Cloud

Railway

Local server

On-premise internal tool

(You can request deployment instructions anytime.)

🤝 Contributing

Pull requests are welcome!
If you find issues, please open a GitHub Issue.

📜 License

MIT License — free to use, modify, and distribute.

⭐ Support

If you like this project, please star the repo ⭐ on GitHub.
It helps a lot!
