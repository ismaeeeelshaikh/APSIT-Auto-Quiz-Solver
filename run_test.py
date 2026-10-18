import requests, os
from dotenv import load_dotenv
load_dotenv(dotenv_path=r"c:\RMU-LMS-Auto-Quiz-Solver\.env")
key = os.environ.get("OPENROUTER_API_KEY", "")
headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json", "HTTP-Referer": "https://github.com"}
models = ["mistralai/mistral-7b-instruct:free","google/gemma-2-9b-it:free","qwen/qwen-2-7b-instruct:free","meta-llama/llama-3.2-3b-instruct:free","google/gemini-2.0-flash-exp:free","deepseek/deepseek-chat:free"]
prompt = "Which is larger? 1. Cat  2. Elephant. Reply ONLY with number 1 or 2."
working = []
for model in models:
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 10}
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers, timeout=15)
        data = r.json()
        if "error" in data:
            print("FAIL [" + model + "] " + str(data["error"].get("message",""))[:70])
        else:
            content = (data["choices"][0]["message"].get("content") or "").strip()
            print("OK   [" + model + "] -> " + repr(content))
            working.append(model)
    except Exception as e:
        print("ERR  [" + model + "] " + str(e))
print()
if working:
    print("USE THIS MODEL: " + working[0])
else:
    print("No free models work. Get Gemini key from aistudio.google.com/app/apikey")
