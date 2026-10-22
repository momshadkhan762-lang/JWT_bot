import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import os
from threading import Thread
from flask import Flask
import requests
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# --- Flask Server for Render Web Service Keep-Alive ---
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot is running successfully!"


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


def keep_alive():
  t = Thread(target=run_flask)
  t.daemon = True
  t.start()


# -----------------------------------------------------

BOT_TOKEN = "8854493990:AAEXLWaA0AouikzHzImIu9wU6Ul_QXSIxRc"

# API URL
API_URL = "https://star-jwt-api1.lovable.app/api/public/token?uid={}&password={}"


def process_via_api(uid, password):
  try:
    url = API_URL.format(uid, password)
    response = requests.get(url, timeout=15)
    if response.status_code == 200:
      res_data = response.json()
      if "token" in res_data:
        return (
            str(uid),
            res_data["token"],
            res_data.get("region", "IND"),
            "SUCCESS",
        )
      else:
        return str(uid), None, "N/A", "Empty Token in Response"
  except requests.exceptions.Timeout:
    return str(uid), None, "N/A", "API Timeout"
  except Exception as e:
    return str(uid), None, "N/A", str(e)
  return str(uid), None, "N/A", "Unknown Error"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  keyboard = [
      ["Process File ⚙️", "Status 👑"],
      ["Shop 🛒", "Help 🆘"],
      ["Cancel ❌"],
  ]
  reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
  
  welcome_text = (
      "🔥 **ELITE JWT TOKEN GENERATOR** 🔥\n"
      "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
      "🚀 *Lightning-Fast High-Speed Token Bot*\n\n"
      "⚡ **Features:**\n"
      "• Instant API Gateway Processing 🌐\n"
      "• Secure Account Management 🛡️\n"
      "• Smart Region Sorting 📊\n\n"
      "📂 Send your `.json` file containing UIDs and passwords below to start! 👇"
  )
  
  await update.message.reply_text(
      welcome_text,
      reply_markup=reply_markup,
      parse_mode="Markdown",
  )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
  text = update.message.text
  if text == "Process File ⚙️":
    await update.message.reply_text(
        "📂 **Ready for Processing!**\n\nSend your `.json` file right here.",
        parse_mode="Markdown"
    )
  elif text == "Status 👑":
    await update.message.reply_text(
        "👑 **Bot Status:** `Online & Blazing Fast` ⚡",
        parse_mode="Markdown"
    )
  elif text == "Shop 🛒":
    await update.message.reply_text(
        "🛒 **VIP Shop & Services**\n\nContact admin for premium tools and APIs.",
        parse_mode="Markdown"
    )
  elif text == "Help 🆘":
    await update.message.reply_text(
        "🆘 **Quick Help:** Upload your `.json` file to instantly get JWT tokens and sorted files.",
        parse_mode="Markdown"
    )
  elif text == "Cancel ❌":
    await update.message.reply_text("❌ Action cancelled.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
  doc = update.message.document
  if not doc or not doc.file_name.endswith(".json"):
    await update.message.reply_text("❌ Please upload a valid `.json` file.")
    return

  msg = await update.message.reply_text(
      "⚡ **Processing Started (Lightning Mode)...**", parse_mode="Markdown"
  )

  file_path = f"temp_{doc.file_name}"
  try:
    file = await context.bot.get_file(doc.file_id)
    await file.download_to_drive(file_path)

    with open(file_path, "r", encoding="utf-8") as f:
      data = json.load(f)

    accounts_to_process = []
    uid_to_password = {}

    if isinstance(data, list):
      for acc in data:
        if isinstance(acc, dict):
          u = acc.get("uid") or acc.get("id")
          t = (
              acc.get("password")
              or acc.get("access_token")
              or acc.get("token")
          )
          if u is not None and t is not None:
            u_str = str(u)
            pwd_str = str(t)
            accounts_to_process.append((u_str, pwd_str))
            uid_to_password[u_str] = pwd_str
    elif isinstance(data, dict):
      for u, t in data.items():
        if u is not None and t is not None:
          u_str = str(u)
          pwd_str = str(t)
          accounts_to_process.append((u_str, pwd_str))
          uid_to_password[u_str] = pwd_str

    total_count = len(accounts_to_process)

    jwt_list = []
    working_list = []
    lost_list = []
    region_tokens = {}
    success_count = 0

    loop = asyncio.get_event_loop()

    # स्पीड बढ़ाने के लिए max_workers को 10 कर दिया है ताकि एक साथ बहुत सारे अकाउंट्स प्रोसेस हों
    with ThreadPoolExecutor(max_workers=10) as executor:
      tasks = [
          loop.run_in_executor(executor, process_via_api, u, pwd)
          for u, pwd in accounts_to_process
      ]
      results = await asyncio.gather(*tasks)

    for u_str, token, reg, err_msg in results:
      pwd = uid_to_password.get(u_str, "")
      if token and token != "N/A":
        jwt_list.append({"token": token})
        working_list.append({"uid": u_str, "password": pwd})
        success_count += 1
        if reg not in region_tokens:
          region_tokens[reg] = []
        region_tokens[reg].append({"uid": u_str, "token": token})
      else:
        lost_list.append({
            "uid": u_str,
            "password": pwd,
            "error_reason": err_msg,
        })

    jwt_file = "jwt_token.json"
    working_file = "working_account.json"
    lost_file = "lost_account.json"
    output_files = []

    with open(jwt_file, "w", encoding="utf-8") as f:
      json.dump(jwt_list, f, indent=4)
      output_files.append(jwt_file)

    with open(working_file, "w", encoding="utf-8") as f:
      json.dump(working_list, f, indent=4)
      output_files.append(working_file)

    with open(lost_file, "w", encoding="utf-8") as f:
      json.dump(lost_list, f, indent=4)
      output_files.append(lost_file)

    for reg_name, reg_list in region_tokens.items():
      reg_file = f"accounts_{reg_name}.json"
      with open(reg_file, "w", encoding="utf-8") as f:
        json.dump(reg_list, f, indent=4)
        output_files.append(reg_file)

    summary = (
        f"🏁 **PROCESSING COMPLETE!**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📊 **Total Accounts:** `{total_count}`\n"
        f"🟢 **Successful Tokens:** `{success_count}`\n"
        f"❌ **Failed/Invalid:** `{total_count - success_count}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 *Blazing Fast & Accurate*"
    )
    await msg.edit_text(summary, parse_mode="Markdown")

    for f_path in output_files:
      if os.path.exists(f_path):
        with open(f_path, "rb") as f_send:
          await update.message.reply_document(document=f_send)
        os.remove(f_path)

  except Exception as e:
    await msg.edit_text(
        f"❌ **Error Occurred:** `{str(e)}`", parse_mode="Markdown"
    )
  finally:
    if os.path.exists(file_path):
      os.remove(file_path)


async def post_init(application):
  print("🤖 Bot started successfully with High-Speed Mode & Keep-Alive!")


def main():
  keep_alive()

  app_bot = (
      ApplicationBuilder()
      .token(BOT_TOKEN)
      .post_init(post_init)
      .build()
  )
  app_bot.add_handler(CommandHandler("start", start))
  app_bot.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
  )
  app_bot.add_handler(
      MessageHandler(filters.Document.FileExtension("json"), handle_document)
  )

  app_bot.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
  main()
                      
