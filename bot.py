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

BOT_TOKEN = "8854493990:AAHyAsEXgkICkD0z1dtp-c3RCtPqSKpc7-4"

# आपकी खरीदी गई ज़िप फाइल वाला एकदम सटीक और ओरिजिनल API URL
API_URL = "https://jwt-api-kx6q.onrender.com/api/get_jwt?guest_uid={}&guest_password={}"


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
        )
  except Exception:
    pass
  return str(uid), None, "N/A"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  keyboard = [
      ["Process File ⚙️", "Status 👑"],
      ["Shop 🛒", "Help 🆘"],
      ["Cancel ❌"],
  ]
  reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
  await update.message.reply_text(
      "👋 **Welcome to GW Token Processor Bot!**\n\nSend your `.json` access"
      " tokens file here to begin.",
      reply_markup=reply_markup,
      parse_mode="Markdown",
  )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
  text = update.message.text
  if text == "Process File ⚙️":
    await update.message.reply_text(
        "📂 Please send your `.json` file containing UIDs and passwords to start"
        " processing."
    )
  elif text == "Status 👑":
    await update.message.reply_text(
        "👑 **Bot Status:** Online & Active (API Gateway Mode)"
    )
  elif text == "Shop 🛒":
    await update.message.reply_text(
        "🛒 Contact admin for premium services & tools."
    )
  elif text == "Help 🆘":
    await update.message.reply_text(
        "🆘 Upload your JSON file containing `uid` and `password` to get JWT"
        " tokens."
    )
  elif text == "Cancel ❌":
    await update.message.reply_text("❌ Action cancelled.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
  doc = update.message.document
  if not doc or not doc.file_name.endswith(".json"):
    await update.message.reply_text("❌ Please upload a valid `.json` file.")
    return

  msg = await update.message.reply_text(
      "📥 **Downloading file...**\n`[▒▒▒▒▒▒▒▒▒▒] 10%`", parse_mode="Markdown"
  )

  file_path = f"temp_{doc.file_name}"
  try:
    file = await context.bot.get_file(doc.file_id)
    await file.download_to_drive(file_path)

    await msg.edit_text(
        "🔍 **Analyzing JSON Structure...**\n`[███▒▒▒▒▒▒▒] 30%`",
        parse_mode="Markdown",
    )

    with open(file_path, "r", encoding="utf-8") as f:
      data = json.load(f)

    accounts_to_process = []
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
            accounts_to_process.append((str(u), str(t)))
    elif isinstance(data, dict):
      for u, t in data.items():
        if u is not None and t is not None:
          accounts_to_process.append((str(u), str(t)))

    total_count = len(accounts_to_process)

    await msg.edit_text(
        f"⚡ **Connecting to Working API Gateway...**\n📊 Total Accounts Found:"
        f" `{total_count}`\n`[██████▒▒▒▒] 60%`",
        parse_mode="Markdown",
    )

    jwt_tokens = {}
    working_accs = {}
    lost_accs = {}
    region_tokens = {}
    success_count = 0

    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(max_workers=5) as executor:
      tasks = [
          loop.run_in_executor(executor, process_via_api, u, pwd)
          for u, pwd in accounts_to_process
      ]
      results = await asyncio.gather(*tasks)

    await msg.edit_text(
        "🔄 **Generating JWT Tokens & Sorting Regions...**\n`[██████████]"
        " 90%`",
        parse_mode="Markdown",
    )

    for u_str, token, reg in results:
      if token and token != "N/A":
        jwt_tokens[u_str] = token
        working_accs[u_str] = token
        success_count += 1
        if reg not in region_tokens:
          region_tokens[reg] = {}
        region_tokens[reg][u_str] = token
      else:
        lost_accs[u_str] = "FAILED"

    jwt_file = "jwt_token.json"
    working_file = "working_account.json"
    lost_file = "lost_account.json"
    output_files = []

    with open(jwt_file, "w", encoding="utf-8") as f:
      json.dump(jwt_tokens, f, indent=4)
      output_files.append(jwt_file)

    with open(working_file, "w", encoding="utf-8") as f:
      json.dump(working_accs, f, indent=4)
      output_files.append(working_file)

    with open(lost_file, "w", encoding="utf-8") as f:
      json.dump(lost_accs, f, indent=4)
      output_files.append(lost_file)

    for reg_name, reg_dict in region_tokens.items():
      reg_file = f"accounts_{reg_name}.json"
      with open(reg_file, "w", encoding="utf-8") as f:
        json.dump(reg_dict, f, indent=4)
        output_files.append(reg_file)

    summary = (
        f"🏁 **Processing Complete!**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📊 **Total Accounts:** `{total_count}`\n"
        f"🟢 **Successful Tokens:** `{success_count}`\n"
        f"❌ **Failed/Invalid:** `{total_count - success_count}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 *Powered by GW & API Gateway*"
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
  print("🤖 Bot started successfully with API Gateway & Keep-Alive!")


def main():
  keep_alive()

  app_bot = (
      ApplicationBuilder()
      .token(BOT_TOKEN)
      .post_init(post_init)
      .build()
  )
  app_bot.add_handler(CommandHandler("start", start))
  app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
  app_bot.add_handler(
      MessageHandler(filters.Document.FileExtension("json"), handle_document)
  )

  app_bot.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
  main()
