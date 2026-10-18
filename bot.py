import re
import os
import time
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from dotenv import load_dotenv

load_dotenv()

# CONFIG
MOODLE_URL         = os.environ.get("MOODLE_URL", "your.university.moodle.url")
PAUSE_AFTER_ANSWER = float(os.environ.get("PAUSE_AFTER_ANSWER", 1.5))
PAUSE_AFTER_NEXT   = float(os.environ.get("PAUSE_AFTER_NEXT",   2.0))
AUTO_CLICK_NEXT    = os.environ.get("AUTO_CLICK_NEXT", "true").lower() == "true"
AUTO_SUBMIT        = os.environ.get("AUTO_SUBMIT",     "false").lower() == "true"

# API Keys
GEMINI_API_KEY     = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY       = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL         = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL   = os.environ.get("OPENROUTER_MODEL", "openrouter/auto")

# AWS Bedrock
AWS_ACCESS_KEY_ID     = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION            = os.environ.get("AWS_REGION", "us-east-1")
AWS_BEDROCK_MODEL     = os.environ.get("AWS_BEDROCK_MODEL", "anthropic.claude-3-5-haiku-20241022-v1:0")


def build_prompt(question, options):
    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    return (
        "You are answering a university MCQ exam question. "
        "Choose the single best answer. Reply with ONLY the number (1, 2, 3, ...) "
        "of the correct option. Nothing else. No explanation.\n\n"
        f"Question: {question}\n\nOptions:\n{options_text}\n\nAnswer (number only):"
    )


def parse_answer(text, num_options):
    text = (text or "").strip()
    match = re.search(r'\d+', text)
    if match:
        idx = int(match.group()) - 1
        if 0 <= idx < num_options:
            return idx
    return -1


def ask_groq(question, options):
    prompt = build_prompt(question, options)
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300,
        "temperature": 0,
    }
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                          json=payload, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        msg = data.get("choices", [{}])[0].get("message", {})
        text = (msg.get("content") or msg.get("reasoning") or "").strip()
        print(f"   [Groq/{GROQ_MODEL}] -> '{text}'")
        return parse_answer(text, len(options))
    except Exception as e:
        print(f"   [Groq error] {e}")
        return -1




def ask_gemini(question, options):
    prompt = build_prompt(question, options)
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        r = requests.post(url, json=payload, timeout=15)
        r.raise_for_status()
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        print(f"   [Gemini] -> '{text}'")
        return parse_answer(text, len(options))
    except Exception as e:
        print(f"   [Gemini error] {e}")
        return -1


def ask_openrouter(question, options):
    prompt = build_prompt(question, options)
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/moodle-quiz-bot",
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 20,
    }
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                          json=payload, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
        msg = data["choices"][0]["message"]
        text = msg.get("content") or msg.get("reasoning") or ""
        text = text.strip()
        used_model = data.get("model", OPENROUTER_MODEL)
        print(f"   [OpenRouter/{used_model}] -> '{text[:60]}'")
        if not text:
            return -1
        return parse_answer(text, len(options))
    except Exception as e:
        print(f"   [OpenRouter error] {e}")
        return -1


def ask_bedrock(question, options):
    prompt = build_prompt(question, options)
    try:
        import boto3
    except ImportError:
        print("   [Bedrock error] 'boto3' is not installed. Run: pip install boto3")
        return -1

    try:
        session = boto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY or None,
            region_name=AWS_REGION or "us-east-1",
        )
        client = session.client("bedrock-runtime")
        response = client.converse(
            modelId=AWS_BEDROCK_MODEL,
            messages=[{
                "role": "user",
                "content": [{"text": prompt}]
            }],
            inferenceConfig={
                "maxTokens": 20,
                "temperature": 0.0,
            }
        )
        content_blocks = response.get("output", {}).get("message", {}).get("content", [])
        text = "".join(b.get("text", "") for b in content_blocks).strip()
        print(f"   [Bedrock/{AWS_BEDROCK_MODEL}] -> '{text}'")
        return parse_answer(text, len(options))
    except Exception as e:
        print(f"   [Bedrock error] {e}")
        return -1


def ask_ai(question, options):
    """Try providers in order: Groq -> Gemini -> AWS Bedrock -> OpenRouter."""
    if GROQ_API_KEY:
        idx = ask_groq(question, options)
        if idx != -1:
            return idx
        print("   [!] Groq failed, trying next provider...")

    if GEMINI_API_KEY:
        idx = ask_gemini(question, options)
        if idx != -1:
            return idx
        print("   [!] Gemini failed, trying next provider...")

    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        idx = ask_bedrock(question, options)
        if idx != -1:
            return idx
        print("   [!] AWS Bedrock failed, trying next provider...")

    if OPENROUTER_API_KEY:
        idx = ask_openrouter(question, options)
        if idx != -1:
            return idx

    print("   [!] All AI providers failed -- please click manually!")
    return -1


def extract_question_data(page):
    question_text   = ""
    option_texts    = []
    option_elements = []

    for sel in [".qtext", ".formulation .qtext", ".formulation p",
                ".questiontext", ".formulation", ".que .content"]:
        el = page.query_selector(sel)
        if el:
            t = el.inner_text().strip()
            if t:
                question_text = t
                break

    answer_container = page.query_selector(".answer")
    if answer_container:
        radios = answer_container.query_selector_all("input[type='radio']")
    else:
        radios = page.query_selector_all(
            ".que input[type='radio'], .formulation input[type='radio']"
        )
    if not radios:
        radios = page.query_selector_all("input[type='radio']")

    JUNK_PHRASES = [
        "clear my choice", "my contacts", "anyone on the site",
        "anyone in my courses", "privacy",
    ]

    for radio in radios:
        r_id    = radio.get_attribute("id")
        r_value = radio.get_attribute("value") or ""
        label   = None

        if r_id:
            label = page.query_selector(f"label[for='{r_id}']")
        if not label:
            try:
                label = radio.evaluate_handle("el => el.closest('label')").as_element()
            except Exception:
                pass
        if not label:
            try:
                label = radio.evaluate_handle(
                    "el => el.parentElement?.querySelector('label') ?? null"
                ).as_element()
            except Exception:
                pass
        if not label:
            try:
                label = radio.evaluate_handle("el => el.nextElementSibling").as_element()
            except Exception:
                pass

        if label:
            raw = label.inner_text().strip()
        elif r_value and r_value not in ("1", "0", "on", "off"):
            raw = r_value.strip()
        else:
            continue

        text = re.sub(r'^([a-eA-E]\s*[.)]\s*|[1-9]\s*[.)]\s*)', '', raw).strip()
        if not text:
            continue
        if any(j in text.lower() for j in JUNK_PHRASES):
            continue

        option_texts.append(text)
        option_elements.append(radio)

    if not question_text:
        print("   [DEBUG] Could not extract question text.")
        try:
            body    = page.query_selector("body")
            snippet = body.inner_text()[:300].replace("\n", " ") if body else "(empty)"
            print(f"   [DEBUG] Page snippet: {snippet}")
        except Exception:
            pass

    if not option_texts:
        total_radios = len(page.query_selector_all("input[type='radio']"))
        print(f"   [DEBUG] No options found. Total radios on page: {total_radios}")

    return question_text, option_texts, option_elements


def is_on_quiz_page(page):
    return "attempt.php" in page.url


def click_answer(page, element):
    try:
        element.scroll_into_view_if_needed()
        time.sleep(0.3)
    except Exception:
        pass

    for strategy in range(5):
        try:
            if strategy == 0:
                element.click()
            elif strategy == 1:
                element.click(force=True)
            elif strategy == 2:
                page.evaluate("el => el.click()", element)
            elif strategy == 3:
                r_id = element.get_attribute("id")
                if r_id:
                    lbl = page.query_selector(f"label[for='{r_id}']")
                    if lbl:
                        lbl.click(force=True)
            elif strategy == 4:
                page.evaluate("""el => {
                    el.checked = true;
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                }""", element)
            time.sleep(0.35)
            if element.is_checked():
                return True
        except Exception:
            pass

    return False


def is_any_current_radio_checked(elements):
    for el in elements:
        try:
            if el.is_checked():
                return True
        except Exception:
            pass
    return False


def click_next(page):
    for sel in [
        "input[value='Next page']", "button:has-text('Next page')",
        "input[value='Next']",      "button:has-text('Next')",
        "[class*='mod_quiz-next-nav']", "input[name='next']",
    ]:
        btn = page.query_selector(sel)
        if btn:
            btn.click()
            print("  -> Next page")
            return True
    return False


def click_finish(page):
    """Clicks 'Finish attempt' on the last quiz question."""
    for sel in [
        "input[value*='Finish attempt']",
        "button:has-text('Finish attempt')",
        "a:has-text('Finish attempt')",
        ".endtestlink",
        "input[value*='Submit all and finish']",
        "button:has-text('Submit all and finish')",
    ]:
        btn = page.query_selector(sel)
        if btn:
            btn_text = (btn.inner_text() or btn.get_attribute("value") or "").lower()
            if "return" in btn_text:
                continue
            try:
                btn.scroll_into_view_if_needed()
                btn.click()
                print("  -> 'Finish attempt' clicked on quiz page")
                time.sleep(2)
                return True
            except Exception:
                pass
    return False


def handle_summary_page(page):
    """
    Handles Moodle's 'Summary of attempt' page (summary.php).
    Clicks 'Submit all and finish' and confirms the popup dialog.
    Never clicks 'Return to attempt'.
    """
    print("\n" + "=" * 55)
    print("  [SUMMARY] Reached Summary of Attempt page!")
    print("=" * 55)

    if not AUTO_SUBMIT:
        print("  [INFO] AUTO_SUBMIT is False. Please click 'Submit all and finish' manually.")
        return False

    print("  [SUBMIT] Auto-submitting quiz: looking for 'Submit all and finish'...")
    time.sleep(1.5)

    # 1. Click 'Submit all and finish' on the summary page
    submitted = False
    selectors_summary = [
        "input[value*='Submit all and finish']",
        "button:has-text('Submit all and finish')",
        ".btn-finishattempt button",
        ".btn-finishattempt input",
        "form[action*='processattempt.php'] button[type='submit']",
        "form[action*='processattempt.php'] input[type='submit']",
        "input[name='finishattemptbutton']",
        "button[name='finishattemptbutton']",
    ]

    for sel in selectors_summary:
        btn = page.query_selector(sel)
        if btn:
            btn_text = (btn.inner_text() or btn.get_attribute("value") or "").lower()
            if "return" in btn_text:
                continue
            try:
                btn.scroll_into_view_if_needed()
                time.sleep(0.5)
                btn.click()
                print("  [1/2] Clicked 'Submit all and finish' button on summary page!")
                submitted = True
                break
            except Exception as e:
                print(f"  [WARN] Click failed with {sel}: {e}")

    if not submitted:
        print("  [!] Could not locate 'Submit all and finish' button.")
        return False

    # 2. Handle the Moodle confirmation modal popup
    print("  [2/2] Waiting for confirmation modal popup...")
    time.sleep(1.5)

    modal_selectors = [
        ".modal-dialog button[data-action='save']",
        ".modal-dialog button:has-text('Submit all and finish')",
        ".modal-footer button:has-text('Submit all and finish')",
        ".modal-dialog .btn-primary",
        ".moodle-dialogue-bd input[value*='Submit all and finish']",
        ".moodle-dialogue-bd button:has-text('Submit all and finish')",
        "div[role='dialog'] button:has-text('Submit all and finish')",
        "div[role='dialog'] .btn-primary",
        "input[value*='Submit all and finish']",
        "button:has-text('Submit all and finish')",
    ]

    for m_sel in modal_selectors:
        try:
            m_btn = page.query_selector(m_sel)
            if m_btn and m_btn.is_visible():
                btn_text = (m_btn.inner_text() or m_btn.get_attribute("value") or "").lower()
                if "cancel" in btn_text or "return" in btn_text:
                    continue
                m_btn.click()
                print("  [SUCCESS] Confirmed 'Submit all and finish'! Quiz submitted!")
                time.sleep(2)
                return True
        except Exception:
            pass

    return True


def try_start_quiz(page):
    # NEVER click if we are on summary.php or review.php
    if "summary.php" in page.url or "review.php" in page.url:
        return False

    for sel in [
        "button:has-text('Attempt quiz')", "input[value='Attempt quiz']",
        "a:has-text('Attempt quiz')",      "button:has-text('Re-attempt quiz')",
        "a:has-text('Re-attempt quiz')",   "input[value='Re-attempt quiz']",
        ".quizstartbuttonbox button",      ".quizstartbuttonbox input",
    ]:
        btn = page.query_selector(sel)
        if btn:
            btn_text = (btn.inner_text() or btn.get_attribute("value") or "").lower()
            if "return" in btn_text:
                continue
            print("\n  [*] Found 'Attempt quiz' -- clicking!")
            btn.click()
            time.sleep(2)
            for cs in ["button:has-text('Start attempt')", "input[value='Start attempt']",
                       "button:has-text('Continue')"]:
                cb = page.query_selector(cs)
                if cb:
                    cb.click()
                    time.sleep(1)
                    break
            return True
    return False



def run_bot():
    providers = []
    if GROQ_API_KEY:
        providers.append(f"Groq ({GROQ_MODEL})")
    if GEMINI_API_KEY:
        providers.append("Gemini 1.5 Flash")
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        providers.append(f"AWS Bedrock ({AWS_BEDROCK_MODEL})")
    if OPENROUTER_API_KEY:
        providers.append(f"OpenRouter ({OPENROUTER_MODEL})")

    print("=" * 60)
    print("  Moodle Quiz Bot")
    print("=" * 60)
    print(f"  Target   : {MOODLE_URL}")
    print(f"  AI       : {' -> '.join(providers) if providers else 'NONE SET'}")
    print(f"  AutoNext : {AUTO_CLICK_NEXT}   AutoSubmit: {AUTO_SUBMIT}")
    print("=" * 60)

    if not providers:
        print("\n[ERROR] No API key set! Add one of these to .env:")
        print("  GROQ_API_KEY          -> console.groq.com                 (FREE, fast)")
        print("  GEMINI_API_KEY        -> aistudio.google.com/app/apikey   (FREE)")
        print("  AWS Bedrock           -> AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY (Uses AWS Credits)")
        print("  OPENROUTER_API_KEY    -> openrouter.ai/keys")
        return

    print("\n[OK] Ready\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page    = browser.new_context().new_page()
        page.goto(MOODLE_URL)

        print("LOG IN -> open your course -> bot will auto-click Attempt quiz")
        print("*** DO NOT CLOSE the browser window! ***\n")
        print("-" * 60)

        question_number  = 0
        last_question    = ""
        scan_counter     = 0
        last_url         = ""
        last_summary_url = ""
        last_review_url  = ""

        while True:
            try:
                page.wait_for_timeout(1000)
                scan_counter += 1
                current_url = page.url

                # Check if we landed on Summary page (summary.php)
                if "summary.php" in current_url:
                    if current_url != last_summary_url:
                        last_summary_url = current_url
                        if handle_summary_page(page):
                            time.sleep(2)
                    continue

                # Check if we landed on Review page (after submission)
                if "review.php" in current_url:
                    if current_url != last_review_url:
                        last_review_url = current_url
                        print("\n" + "=" * 60)
                        print("  [SUCCESS] Quiz submitted! Review page loaded.")
                        print("  [READY] Browser stays open for your other experiments!")
                        print("  -> Navigate to your next quiz in Chrome, bot will auto-solve it.")
                        print("=" * 60 + "\n")
                        # Reset question tracker for the next quiz
                        question_number = 0
                        last_question   = ""
                    time.sleep(2)
                    continue

                if current_url != last_url:
                    last_url = current_url
                    if "mod/quiz" in current_url and "attempt.php" not in current_url and "summary.php" not in current_url and "review.php" not in current_url:
                        time.sleep(1)
                        if try_start_quiz(page):
                            print("  [OK] Quiz started!")
                            question_number = 0
                            last_question   = ""
                            time.sleep(2)
                            continue



                if scan_counter % 5 == 0:
                    print(".", end="", flush=True)

                if not is_on_quiz_page(page):
                    continue

                question, options, elements = extract_question_data(page)

                if not question or not options or question == last_question:
                    continue

                print("")
                question_number += 1
                last_question = question

                print(f"\nQ{question_number}: {question[:120]}{'...' if len(question) > 120 else ''}")
                for i, opt in enumerate(options):
                    print(f"   {i+1}. {opt[:90]}")

                print("   [BOT] Asking AI...")
                answer_idx = ask_ai(question, options)

                if answer_idx == -1:
                    print("   [WAIT] Please click the answer manually...")
                    while True:
                        page.wait_for_timeout(500)
                        if is_any_current_radio_checked(elements):
                            print("   [OK] Selection detected -- continuing...")
                            break
                    if AUTO_CLICK_NEXT:
                        time.sleep(PAUSE_AFTER_NEXT)
                        if not click_next(page) and AUTO_SUBMIT:
                            click_finish(page)
                    last_question = question
                    continue

                print(f"   [ANS] Option {answer_idx + 1}: {options[answer_idx][:70]}")
                time.sleep(PAUSE_AFTER_ANSWER)

                selected = click_answer(page, elements[answer_idx])
                if selected:
                    print("   [OK] Answer verified!")
                else:
                    print("   [WARN] Could not verify -- click manually if wrong.")
                    time.sleep(2)

                if AUTO_CLICK_NEXT:
                    time.sleep(PAUSE_AFTER_NEXT)
                    if not click_next(page) and AUTO_SUBMIT:
                        click_finish(page)

            except PlaywrightTimeout:
                continue
            except KeyboardInterrupt:
                print("\n[STOP] Stopped by user.")
                break
            except Exception as e:
                print(f"\n[Error] {e}")
                time.sleep(2)

        try:
            browser.close()
        except Exception:
            pass
        print("\n[DONE]")


if __name__ == "__main__":
    run_bot()