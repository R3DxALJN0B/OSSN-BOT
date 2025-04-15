import os
import re
import subprocess
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)
bot_app = Application.builder().token(TOKEN).build()

@app.route("/")
def home():
    return "Bot is running!"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    bot_app.update_queue.put(update)
    return "OK"

def detect_input_type(user_input: str):
    if re.match(r"^\+?\d{6,15}$", user_input):
        return "phone"
    elif "@" in user_input and "." in user_input:
        return "email"
    else:
        return "username"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل اسم مستخدم أو بريد إلكتروني أو رقم هاتف للبحث عنه.")

async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    input_type = detect_input_type(user_input)
    await update.message.reply_text(f"جارٍ البحث عن: {user_input} (نوع الإدخال: {input_type})")

    try:
        if input_type == "username":
            result = subprocess.run(["python3", "tools/sherlock/sherlock.py", user_input, "--print-found"],
                                    capture_output=True, text=True, timeout=300)
        elif input_type == "email":
            result = subprocess.run(["python3", "tools/holehe/holehe.py", user_input],
                                    capture_output=True, text=True, timeout=300)
        elif input_type == "phone":
            result = subprocess.run(["python3", "tools/PhoneInfoga/phoneinfoga.py", "scan", "-n", user_input],
                                    capture_output=True, text=True, timeout=300)
        else:
            await update.message.reply_text("نوع الإدخال غير مدعوم.")
            return

        output = result.stdout.strip() or "لم يتم العثور على نتائج."
        await update.message.reply_text(output[:4000])

    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء البحث: {e}")

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))

if __name__ == "__main__":
    bot_app.run_polling()
