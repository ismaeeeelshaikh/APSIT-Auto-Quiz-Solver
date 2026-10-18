# 🤖 Moodle LMS Auto Quiz Solver

An intelligent, fully automated quiz bot designed for **Moodle LMS** (v3.x & v4.x). It automatically detects quiz questions, queries top LLMs (Groq, Google Gemini, AWS Bedrock, OpenRouter), clicks the correct answer with verification, advances pages, and submits the attempt.

> 🎓 Tested and compatible with **A. P. Shah Institute of Technology (APSIT)**, **Rawalpindi Medical University (RMU)**, and any standard university Moodle portal.

---

## ✨ Features

- ⚡ **Multi-AI Provider Support**:
  - **Groq (Recommended)**: Ultra-fast (~0.3s response) with models like `openai/gpt-oss-120b` and `llama-3.1-8b-instant` (100% Free).
  - **Google Gemini**: Reliable `gemini-1.5-flash` via Google AI Studio (100% Free).
  - **AWS Bedrock**: Universal Converse API support for Anthropic Claude 3.5 Haiku, Meta Llama 3, Amazon Nova (ideal for AWS Promotional Credits).
  - **OpenRouter**: Flexible multi-model gateway.
- 🎯 **End-to-End Automation**:
  - **Auto-Start**: Automatically clicks *"Attempt quiz"* and modal *"Start attempt"*.
  - **Auto-Solve**: Scrapes question text + options, formats the prompt, and selects the answer.
  - **Verified Click**: Multi-strategy click engine ensures radio button is actually checked.
  - **Auto-Next**: Automatically advances through multi-page quizzes.
  - **Auto-Submit**: Detects last question, clicks *"Finish attempt"*, navigates the Summary page, and confirms the *"Submit all and finish"* popup.
- 🔄 **Continuous Multi-Quiz Mode**:
  - Keeps the browser open and logged in after submitting.
  - Simply click on your next experiment/quiz in Chrome and the bot will immediately begin solving it!
- 🛡️ **Fail-Safe & Human-in-the-Loop**:
  - If an AI provider is unreachable or encounters an error, the bot falls back to the next provider.
  - If all providers fail, it waits for your manual click and resumes seamlessly.

---

## 📋 Prerequisites

- **Python 3.9+**
- **Chromium browser** (installed automatically via Playwright)
- At least **one** free API key:
  - 👉 **Groq (Recommended, 30s setup, 100% Free)**: [console.groq.com/keys](https://console.groq.com/keys)
  - 👉 **Google Gemini (100% Free)**: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
  - 👉 **AWS Bedrock**: Use your AWS credentials & promotional credits.

---

## 🚀 Quick Start

### 1. Clone & Navigate
```bash
git clone https://github.com/Shahzaib-XVII/RMU-LMS-Auto-Quiz-Solver.git
cd RMU-LMS-Auto-Quiz-Solver
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure `.env`
Copy the example configuration:
```bash
cp .env.example .env
```
Open `.env` and set your Moodle URL and chosen AI provider key:

```env
# Your University Moodle Portal
MOODLE_URL=https://elearn.apsit.edu.in/moodle/

# --- OPTION 1: Groq (Recommended - 100% Free, Instant) ---
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b

# --- Bot Settings ---
PAUSE_AFTER_ANSWER=1.5
PAUSE_AFTER_NEXT=2.0
AUTO_CLICK_NEXT=true
AUTO_SUBMIT=true
```

### 4. Test Your AI Key (Optional)
Verify your Groq API key and model before launching the browser:
```bash
python test_groq.py
```

### 5. Run the Bot
```bash
python bot.py
```

---

## 💡 How It Works During Quizzes

1. **Browser Launches**: Playwright launches a visible Chromium browser window.
2. **Log In**: Log in to your university portal in that browser window.
3. **Navigate to Quiz**: Open your course and click on any experiment or quiz.
4. **Auto-Pilot**:
   - The bot automatically clicks **"Attempt quiz"** / **"Start attempt"**.
   - It reads each question, prompts the AI, verifies the selected radio button, and clicks **"Next page"**.
   - On the last question, it clicks **"Finish attempt"**.
   - On the summary page, it clicks **"Submit all and finish"** and confirms the modal popup dialog.
5. **Next Quiz**: The browser stays open. Navigate to the next quiz and the bot automatically begins solving it!
6. **Stop**: Press `Ctrl + C` in your terminal when you are done.

---

## ⚙️ Configuration Reference (`.env`)

| Variable | Default | Description |
|---|---|---|
| `MOODLE_URL` | *(required)* | Your university's Moodle base URL |
| `GROQ_API_KEY` | *(optional)* | Groq API Key (starts with `gsk_`) |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Groq model (`openai/gpt-oss-120b`, `llama-3.1-8b-instant`) |
| `GEMINI_API_KEY` | *(optional)* | Google Gemini API Key (starts with `AIza...`) |
| `AWS_ACCESS_KEY_ID` | *(optional)* | AWS Access Key for Bedrock |
| `AWS_SECRET_ACCESS_KEY` | *(optional)* | AWS Secret Key for Bedrock |
| `AWS_REGION` | `us-east-1` | AWS Bedrock Region |
| `AWS_BEDROCK_MODEL` | `anthropic.claude-3-5-haiku-20241022-v1:0` | Bedrock Foundation Model ID |
| `OPENROUTER_API_KEY` | *(optional)* | OpenRouter API Key |
| `OPENROUTER_MODEL` | `openrouter/auto` | OpenRouter Model ID |
| `PAUSE_AFTER_ANSWER` | `1.5` | Delay in seconds after selecting an answer |
| `PAUSE_AFTER_NEXT` | `2.0` | Delay in seconds before clicking "Next page" |
| `AUTO_CLICK_NEXT` | `true` | Automatically advance to next page |
| `AUTO_SUBMIT` | `true` | Automatically submit and confirm on completion |

---

## 🛠️ Troubleshooting

- **"Connection closed while reading from the driver"**:
  - Do **NOT** close the Chrome browser window manually while the bot is running.
- **Bot is printing dots (`.....`)**:
  - The bot is scanning the page. Ensure you are on the quiz page (`attempt.php`) or the quiz start page.
- **Answer could not be selected**:
  - The bot will display a `[WAIT]` prompt. Simply click the answer manually in the browser, and the bot will immediately resume automatic progression.
- **Testing different models**:
  - Run `python test_groq.py` to test any Groq model before running quizzes.

---

## ⚠️ Disclaimer

This project is created strictly for **educational and research purposes**. Automated interaction with academic portals may be subject to your institution's acceptable use policies and academic honor codes. Use responsibly.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.