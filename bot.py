import asyncio
import binascii
import json
import os
from threading import Thread
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from flask import Flask
import my_pb2
import output_pb2
import requests
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import warnings
from urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter("ignore", InsecureRequestWarning)

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

BOT_TOKEN = "8854493990:AAGWwdmHb-N7T_ATNEPRcaB8rLKpxadYPz4"

AES_KEY = b"Yg&tc%Deuh6%Zc^8"
AES_IV = b"6oyZDr22EychjM%"


def get_token(password, uid):
  try:
    url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
    headers = {
        "Host": "100067.connect.garena.com",
        "User-Agent": "GarenaMSDK/4.0.19P4 (Vivo Y15c; Android 12; en;IN;)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "close",
    }
    data = {
        "uid": uid,
        "password": password,
        "response_type": "token",
        "client_type": "2",
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        "client_id": "100067",
    }
    response = requests.post(url, headers=headers, data=data, verify=False, timeout=10)
    if response.status_code != 200:
      return None
    return response.json()
  except Exception:
    return None


def get_token_inspect_data(access_token):
  """Inspect access token to get open_id and platform info"""
  try:
    url = f"https://100067.connect.garena.com/oauth/token/inspect?token={access_token}"
    headers = {
        "User-Agent": "GarenaMSDK/4.0.19P4 (Vivo Y15c; Android 12; en;IN;)",
        "Connection": "close",
    }
    response = requests.get(url, headers=headers, verify=False, timeout=10)
    if response.status_code == 200:
      data = response.json()
      if "open_id" in data and "platform" in data and "uid" in data:
        return data
  except Exception:
    pass
  return None


def encrypt_message(key, iv, plaintext):
  cipher = AES.new(key, AES.MODE_CBC, iv)
  return cipher.encrypt(pad(plaintext, AES.block_size))


def parse_response(response_content):
  response_dict = {}
  lines = response_content.split("\n")
  for line in lines:
    if ":" in line:
      key, value = line.split(":", 1)
      response_dict[key.strip()] = value.strip()
  return response_dict


def process_access_token(password, uid):
  token_data = get_token_inspect_data(password)
  if not token_data:
    grant_data = get_token(password, uid)
    if grant_data and "access_token" in grant_data:
      access_token = grant_data["access_token"]
      token_data = get_token_inspect_data(access_token)
    else:
      access_token = password
  else:
    access_token = password

  if not token_data:
    return str(uid), None, "N/A"

  open_id = token_data["open_id"]
  platform_type = token_data.get("platform")
  uid_str = str(uid or token_data.get("uid"))

  try:
    game_data = my_pb2.GameData()
    game_data.timestamp = "2025-05-29T10:00:00Z"
    game_data.game_name = "free fire"
    game_data.game_version = 1
    game_data.version_code = "1.126.2"
    game_data.os_info = "Android OS 11 / API-30 (RKQ1.201105.002/7112)"
    game_data.device_type = "Handheld"
    game_data.network_provider = "JIO"
    game_data.connection_type = "MOBILE"
    game_data.screen_width = 720
    game_data.screen_height = 1600
    game_data.dpi = "280"
    game_data.cpu_info = "ARM Cortex-A55"
    game_data.total_ram = 4096
    game_data.gpu_name = "Adreno (TM) 610"
    game_data.gpu_version = "OpenGL ES 3.2"
    game_data.user_id = uid_str
    game_data.ip_address = "182.75.115.10"
    game_data.language = "en"
    game_data.open_id = open_id
    game_data.access_token = access_token
    game_data.platform_type = platform_type
    game_data.device_form_factor = "Handheld"
    game_data.device_model = "ASUS_Z01QD"
    game_data.field_60 = 30000
    game_data.field_61 = 27500
    game_data.field_62 = 1940
    game_data.field_63 = 720
    game_data.field_64 = 28000
    game_data.field_65 = 30000
    game_data.field_66 = 28000
    game_data.field_67 = 30000
    game_data.field_70 = 4
    game_data.field_73 = 2
    game_data.library_path = "/data/app/~~X==/lib/arm64"
    game_data.field_76 = 1
    game_data.apk_info = "2f4a7f349f3a9e5b7c8d1e2f3a4b5c6d"
    game_data.field_78 = 6
    game_data.field_79 = 1
    game_data.os_architecture = "64"
    game_data.build_number = "2022041315"
    game_data.field_85 = 1
    game_data.graphics_backend = "OpenGL"
    game_data.max_texture_units = 16384
    game_data.rendering_api = 4
    game_data.encoded_field_89 = b"\x10\x01"
    game_data.field_92 = 8999
    game_data.marketplace = "3rd_party"
    game_data.encryption_key = "Jp2DT7..."
    game_data.total_storage = 64000
    game_data.field_97 = 1
    game_data.field_98 = 1
    game_data.field_99 = str(platform_type)
    game_data.field_100 = str(platform_type)

    serialized_data = game_data.SerializeToString()
    encrypted_data = encrypt_message(AES_KEY, AES_IV, serialized_data)
    hex_encrypted_data = binascii.hexlify(encrypted_data).decode("utf-8")
    edata = bytes.fromhex(hex_encrypted_data)

    url = "https://loginbp.ggblueshark.com/MajorLogin"
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; ASUS_Z01QD Build/PI)",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/octet-stream",
        "Expect": "100-continue",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB55",
    }
    response = requests.post(url, headers=headers, data=edata, timeout=15)

    if response.status_code == 200:
      example_msg = output_pb2.Lokesh()
      example_msg.ParseFromString(response.content)
      response_dict = parse_response(str(example_msg))
      jwt_tok = response_dict.get("token")
      region_name = response_dict.get("region", "N/A")
      return uid_str, jwt_tok, region_name
  except Exception:
    pass

  return uid_str, None, "N/A"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  keyboard = [
      ["Process File ⚙️", "Status 👑"],
      ["Shop 🛒", "Help 🆘"],
      ["Cancel ❌"],
  ]
  reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
  await update.message.reply_text(
      "👋 Welcome!\n\nSend your `.json` access tokens file here.",
      reply_markup=reply_markup,
  )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
  doc = update.message.document
  if not doc or not doc.file_name.endswith(".json"):
    await update.message.reply_text("❌ Please upload a valid `.json` file.")
    return

  msg = await update.message.reply_text("📥 Downloading and processing file...")
  file_path = f"temp_{doc.file_name}"
  try:
    file = await context.bot.get_file(doc.file_id)
    await file.download_to_drive(file_path)

    with open(file_path, "r", encoding="utf-8") as f:
      data = json.load(f)

    accounts_to_process = []
    
    # --- स्क्रीनशॉट वाले फॉर्मेट (uid और password की लिस्ट) के लिए फिक्स ---
    if isinstance(data, list):
      for acc in data:
        if isinstance(acc, dict):
          u = acc.get("uid")
          t = acc.get("password")
          if u is not None and t is not None:
            accounts_to_process.append((str(t), str(u)))
    elif isinstance(data, dict):
      for u, t in data.items():
        if u is not None and t is not None:
          accounts_to_process.append((str(t), str(u)))
    # -----------------------------------------------------------------

    total_count = len(accounts_to_process)
    jwt_tokens = {}
    working_accs = {}
    lost_accs = {}
    region_tokens = {}
    success_count = 0

    loop = asyncio.get_event_loop()
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=5) as executor:
      tasks = [
          loop.run_in_executor(executor, process_access_token, pwd, u)
          for pwd, u in accounts_to_process
      ]
      results = await asyncio.gather(*tasks)

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
        f"📊 **Total Accounts:** {total_count}\n"
        f"🟢 **Successful Tokens:** {success_count}\n"
        f"❌ **Failed:** {total_count - success_count}"
    )
    await msg.edit_text(summary, parse_mode="Markdown")

    for f_path in output_files:
      if os.path.exists(f_path):
        with open(f_path, "rb") as f_send:
          await update.message.reply_document(document=f_send)
        os.remove(f_path)

  except Exception as e:
    await msg.edit_text(f"❌ Error: {str(e)}")
  finally:
    if os.path.exists(file_path):
      os.remove(file_path)


async def post_init(application):
  print("🤖 Bot started successfully with OB55 & Flask Keep-Alive!")


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
      MessageHandler(filters.Document.FileExtension("json"), handle_document)
  )

  app_bot.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
  main()
