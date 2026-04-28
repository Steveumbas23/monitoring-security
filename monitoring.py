import datetime
import os
import subprocess
from pathlib import Path

import google.generativeai as genai
import requests


def load_env_file(path=".env"):
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_env_file()

# Konfigurasi API Gemini
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY belum diatur di file .env")

genai.configure(api_key=gemini_api_key)

model = genai.GenerativeModel(model_name="gemini-2.5-flash")

def get_ssh_attempts():
    result = subprocess.check_output("grep 'Failed password' /var/log/auth.log | tail -n 10", shell=True)
    return result.decode()

def get_genai_analysis(log_text):
    try:
        response = model.generate_content(f"Ada percobaan login brute force:\n{log_text}\nApa yang sebaiknya saya lakukan?, responnya jangan terlalu panjang")
        return response.text
    except Exception as e:
        return f"⚠️ Gagal mendapatkan analisis dari Gemini: {e}"

def send_whatsapp(message):
    token = os.getenv("FONNTE_TOKEN")
    target = os.getenv("WHATSAPP_TARGET")

    if not token:
        raise ValueError("FONNTE_TOKEN belum diatur di file .env")
    if not target:
        raise ValueError("WHATSAPP_TARGET belum diatur di file .env")

    payload = {
        "target": target,
        "message": message,
    }
    headers = {"Authorization": token}
    r = requests.post("https://api.fonnte.com/send", data=payload, headers=headers)
    return r.status_code

# Eksekusi semua
log = get_ssh_attempts()
ai_response = get_genai_analysis(log)

full_message = f"[{datetime.datetime.now()}] ⚠️ Percobaan Login Detected!\n\n{log}\n\n🧠 Gemini says:\n{ai_response}"

send_whatsapp(full_message)
