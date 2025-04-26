import sqlite3
import uuid
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ContextTypes

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = "YOUR_BOT_TOKEN"  # Замените на токен вашего бота
SUPPORT_GROUP_ID = -1234567890123  # Замените на ID вашей группы
ADMIN_IDS = [123456789, 987654321]  # Замените на ID администраторов

# Инициализация базы данных SQLite
def init_db():
    conn = sqlite3.connect('tickets.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tickets
                 (ticket_id TEXT PRIMARY KEY, user_id INTEGER, username TEXT, support_type TEXT,
                  status TEXT, messages TEXT)''')
    conn.commit()
    conn.close()

init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Обратиться в поддержку", callback_data="support")],
        [InlineKeyboardButton("Техническая поддержка", callback_data="tech_support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Добро пожаловать! Выберите тип поддержки:",
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    ticket_id = str(uuid.uuid4())[:8]
    user_id = query.from_user.id
    username = query.from_user.username or "Без имени"

    if query.data in ["support", "tech_support"]:
        conn = sqlite3.connect('tickets.db')
        c = conn.cursor()
        c.execute("INSERT INTO tickets (ticket_id, user_id, username, support_type, status, messages) VALUES (?, ?, ?, ?, ?, ?)",
                  (ticket_id, user_id, username, query.data, "open", ""))
        conn.commit()
        conn.close()

        support_type = "Техническая поддержка" if query.data == "tech_support" else "Общая поддержка"
        await query.message.reply_text(
            f"Опишите вашу проблему (тикет #{ticket_id})."
        )
        context.user_data["ticket_id"] = ticket_id
        context.user_data["support_type"] = query.data

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "ticket_id" not in context.user_data:
        await update.message.reply_text("Пожалуйста, начните с команды /start и выберите тип поддержки.")
        return

    ticket_id = context.user_data["ticket_id"]
    support_type = context.user_data["support_type"]
    user_message = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Без имени"

    # Сохранение сообщения в базе
    conn = sqlite3.connect('tickets.db')
    c = conn.cursor()
    c.execute("SELECT messages FROM tickets WHERE ticket_id = ?", (ticket_id,))
    messages = c.fetchone()[0]
    messages += f"User: {user_message}\n"
    c.execute("UPDATE tickets SET messages = ? WHERE ticket_id = ?", (messages, ticket_id))
    conn.commit()
    conn.close()

    # Отправка тикета в группу
    group_message = (
        f"Тикет #{ticket_id}\n"
        f"Тип: {'Техническая поддержка' if support_type == 'tech_support' else 'Общая поддержка'}\n"
        f"Пользователь: @{username} (ID: {user_id})\n"
        f"Сообщение: {user_message}\n"
        f"Для ответа используйте: /reply {ticket_id} <ваш ответ>"
    )
    await context.bot.send_message(chat_id=SUPPORT_GROUP_ID, text=group_message)
    await update.message.reply_text("Ваш запрос отправлен! Мы ответим в ближайшее время.")

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != SUPPORT_GROUP_ID:
        await update.message.reply_text("Эта команда доступна только в группе поддержки.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Используйте: /reply <ticket_id> <ответ>")
        return

    ticket_id = args[0]
    response = " ".join(args[1:])

    conn = sqlite3.connect('tickets.db')
    c = conn.cursor()
    c.execute("SELECT user_id, messages FROM tickets WHERE ticket_id = ?", (ticket_id,))
    result = c.fetchone()
    if not result:
        await update.message.reply_text("Тикет не найден.")
        conn.close()
        return

    user_id, messages = result
    messages += f"Support: {response}\n"
    c.execute("UPDATE tickets SET messages = ? WHERE ticket_id = ?", (messages, ticket_id))
    conn.commit()
    conn.close()

    await context.bot.send_message(chat_id=user_id, text=f"Ответ на тикет #{ticket_id}:\n{response}")
    await update.message.reply_text(f"Ответ отправлен пользователю (тикет #{ticket_id}).")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступ запрещён.")
        return

    keyboard = [
        [InlineKeyboardButton("Список открытых тикетов", callback_data="list_tickets")],
        [InlineKeyboardButton("Закрыть тикет", callback_data="close_ticket")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Админ-панель:", reply_markup=reply_markup)

async def admin_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "list_tickets":
        conn = sqlite3.connect('tickets.db')
        c = conn.cursor()
        c.execute("SELECT ticket_id, user_id, username, support_type, status FROM tickets WHERE status = 'open'")
        tickets = c.fetchall()
        conn.close()

        if not tickets:
            await query.message.reply_text("Нет открытых тикетов.")
            return

        response = "Открытые тикеты:\n"
        for ticket in tickets:
            response += (
                f"Тикет #{ticket[0]} | Тип: {ticket[3]} | Пользователь: @{ticket[2]} (ID: {ticket[1]})\n"
            )
        await query.message.reply_text(response)

    elif query.data == "close_ticket":
        await query.message.reply_text("Введите ID тикета для закрытия: /close <ticket_id>")
        context.user_data["admin_action"] = "close_ticket"

async def close_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступ запрещён.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Используйте: /close <ticket_id>")
        return

    ticket_id = context.args[0]
    conn = sqlite3.connect('tickets.db')
    c = conn.cursor()
    c.execute("UPDATE tickets SET status = 'closed' WHERE ticket_id = ?", (ticket_id,))
    if c.rowcount == 0:
        await update.message.reply_text("Тикет не найден.")
    else:
        conn.commit()
        await update.message.reply_text(f"Тикет #{ticket_id} закрыт.")
    conn.close()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("reply", reply))
    application.add_handler(CommandHandler("close", close_ticket))
    application.add_handler(CallbackQueryHandler(button_callback, pattern="^(support|tech_support)$"))
    application.add_handler(CallbackQueryHandler(admin_button_callback, pattern="^(list_tickets|close_ticket)$"))
    application.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_user_message))
    application.add_error_handler(error_handler)

    application.run_polling()

if __name__ == "__main__":
    main()