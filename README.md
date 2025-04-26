# support-bot
A Python-based Telegram bot for customer and technical support with an integrated admin panel. Users can create support tickets (general or technical)

🗳️ Create and manage support tickets (general/technical) with unique IDs.
💬 Support staff can respond to users using /reply <ticket_id> <response> in a Telegram group.
🔧 Admin panel (/admin) for viewing open tickets and closing them (/close <ticket_id>).
📦 SQLite database for storing tickets and message history.
🌐 Multilingual support (e.g., Cyrillic text) with UTF-8 encoding.
⚡ Built with python-telegram-bot v22.0 for reliability and modern Telegram API support.

Python 3.12+
python-telegram-bot v22.0
SQLite

Setup:

Clone the repo and install dependencies: pip install python-telegram-bot>=22.0.
Configure BOT_TOKEN, SUPPORT_GROUP_ID, and ADMIN_IDS in the script.
Run: python app.py.
See for detailed instructions.

Additional Notes
Why This Description?
It’s concise (fits GitHub’s repo description field) and highlights the bot’s core functionality.
It emphasizes ease of setup and modern tech (Python 3.12, python-telegram-bot v22.0).
It includes emojis to make it visually appealing and scannable.
It mentions the admin panel and SQLite, which are key differentiators.
The “Use Case” helps attract relevant users (e.g., businesses or communities).
README.md Suggestion:
For a complete GitHub repo, you should include a README.md with:
Detailed setup instructions (e.g., getting a bot token from @BotFather, finding group IDs).
Example usage (screenshots or sample commands like /start, /reply, /admin).
Troubleshooting tips (e.g., ensuring UTF-8 encoding, Python version).
Contribution guidelines and license details.
If you want, I can generate a full README.md or other files (e.g., .gitignore, requirements.txt) to complement the description.
