import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=r"c:\RMU-LMS-Auto-Quiz-Solver\.env")

key = os.environ.get("GROQ_API_KEY", "").strip()
model = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant").strip()

print("=" * 50)
print("Groq API Quick Tester")
print("=" * 50)

if not key:
    print("[ERROR] GROQ_API_KEY is empty in .env!")
    print("Please open .env and paste your Groq key:")
    print("  GROQ_API_KEY=gsk_...")
    print("Get your free key at: https://console.groq.com/keys")
    exit(1)

print(f"Key detected: {key[:8]}...{key[-4:]}")
print(f"Model: {model}")
print("\nTesting with a sample quiz question...")

headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
}

prompt = (
    "Choose the correct option number (1, 2, 3, or 4). Reply with ONLY the number.\n\n"
    "Question: What is the capital of France?\n"
    "1. Berlin\n"
    "2. Madrid\n"
    "3. Paris\n"
    "4. Rome\n\n"
    "Answer:"
)

payload = {
    "model": model,
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": 300,
    "temperature": 0,
}

try:
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      json=payload, headers=headers, timeout=15)
    r.raise_for_status()
    data = r.json()
    msg = data["choices"][0]["message"]
    reply = (msg.get("content") or msg.get("reasoning") or "").strip()
    print(f"\n[SUCCESS] Groq answered: '{reply}'")
    print("Your Groq API key is working perfectly!")
    print("\nYou can now run the bot with: python bot.py")

except Exception as e:
    print(f"\n[ERROR] Groq request failed: {e}")
    if 'r' in locals() and hasattr(r, 'text'):
        print(f"Details: {r.text}")
