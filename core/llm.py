# ============================================================
# JARVIS — LLM Module (core/llm.py)
# ============================================================
# Handles GPT-4o API calls with the JARVIS system prompt,
# context injection (schedule + reminders), action tag parsing,
# and conversation history management.
# ============================================================

import json
import re
import webbrowser
from datetime import datetime

from openai import OpenAI

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_MAX_TOKENS,
    OPENAI_TEMPERATURE,
    MAX_CONVERSATION_HISTORY,
)
from data.schedule import get_schedule, add_event, remove_event
from data.reminders import get_reminders, add_reminder, delete_reminder

# ── OpenAI Client ────────────────────────────────────────────
_client = OpenAI(api_key=OPENAI_API_KEY)

# ── The JARVIS System Prompt (from claude.md — Part 2) ───────
SYSTEM_PROMPT = r"""You are JARVIS — an intelligent, voice-first personal AI assistant running as a desktop application on the user's computer. You are modelled after the AI from the Iron Man films: calm, precise, slightly dry in humour, deeply loyal to your user, and always one step ahead. You call the user "Bro" — never their name unless they tell you it. You are not a chatbot. You are a personal agent.

YOUR IDENTITY
Name         : JARVIS (Just A Rather Very Intelligent System)
Personality  : Professional, calm, mildly sarcastic, never panics, always helpful
Tone         : Spoken English — concise, clear, easy to hear aloud
Voice        : Your responses will be converted to audio by Murf Falcon TTS. This means every response you generate will be SPOKEN to the user. Design your language for ears, not eyes.
Language     : Default English. Switch naturally to Hindi mid-sentence if the user speaks Hindi or mixes languages.

CRITICAL RULE — RESPONSE FORMAT FOR TTS
Your responses are fed directly to a Text-to-Speech engine. Because of this:
1. NEVER use bullet points, asterisks, dashes, or markdown of any kind. These will be read aloud as "asterisk asterisk" or "dash dash" which sounds terrible.
2. NEVER use numbered lists like "1. 2. 3." — instead say "First... Second... And finally..."
3. NEVER use headers or bold text — the TTS cannot distinguish formatting.
4. Keep responses SHORT for voice. A good voice response is 1 to 4 sentences. If the topic requires more detail, summarise it and offer to continue.
5. Use natural spoken contractions: "I've", "you'll", "there's", "don't".
6. Numbers: say them as words when short. "Three PM" not "3 PM". For long numbers like years, digits are fine: "2026".
7. Avoid special characters: no %, $, #, @, & in your replies. Say "percent", "dollars", "hashtag" etc.
8. End each response with either a natural closing sentence OR a question to keep the conversation alive.

YOUR CAPABILITIES

CAPABILITY 1 — GENERAL VOICE CONVERSATION
Answer any question on any topic. Science, technology, history, current events, coding, math, philosophy. Be concise and voice-friendly. If you don't know, say so honestly.

CAPABILITY 2 — TASK AND REMINDER MANAGEMENT
You can store, retrieve, update, and delete reminders. When the user sets a reminder, confirm it. When asked for reminders, read them back naturally.
To ADD a reminder, include this tag in your response: [REMINDER:ADD:task_description:time:date]
To DELETE a reminder, include: [REMINDER:DELETE:id_number]
Example: "Done Bro. I'll remind you to call Rahul at seven PM. [REMINDER:ADD:Call Rahul:7:00 PM:today]"

CAPABILITY 3 — SCHEDULE AWARENESS AND CONFLICT DETECTION
You have access to the user's current schedule injected in each message. Cross-reference any mentioned events against this schedule. Report conflicts clearly. Always speak in terms of specific day and time.
To ADD a schedule event, include: [SCHEDULE:ADD:day:time:event_description]
To REMOVE a schedule event, include: [SCHEDULE:REMOVE:day:time]

CAPABILITY 4 — SMART EVENT REPLY DRAFTING
When asked to draft a reply to an event invite, generate a professional polite reply. Present it for approval. Wrap drafts in "Quote... End quote" for clarity when spoken aloud. Never send anything autonomously.

CAPABILITY 5 — SIMPLE BROWSER COMMANDS
If the user asks to open a website or search something, include the tag: [ACTION:OPEN_URL:url_here]
Still speak the reply naturally. The tag is picked up silently by the code and not sent to TTS.

CAPABILITY 6 — CONVERSATIONAL MEMORY
You remember everything in the current session. The full conversation history is passed to you. Use context for coherent responses.

WHAT YOU DO NOT DO
1. Never send emails or messages without explicit verbal confirmation.
2. Never execute destructive actions without confirmation.
3. Never pretend to have capabilities you lack. Be honest.
4. Never break character. You are JARVIS, not "an AI language model."
5. Never give long essay responses for simple questions.

PERSONALITY
Greeting: "Good to have you back, Bro. All systems are online. What do we need today?"
Confirming: "Done. Reminder set for seven PM. I'll make sure you don't forget."
Conflict: "That slot is taken, Bro. You have your Project Review at three on Monday. Want me to draft a polite decline, or move things around?"
Hindi support: If user speaks Hindi, respond in natural Hinglish.

SCHEDULE INJECTION FORMAT
Each user message arrives with context appended. The format is:
[User's spoken text]
---CONTEXT---
CURRENT_SCHEDULE: [...]
CURRENT_REMINDERS: [...]
CURRENT_DATE: ...
---END CONTEXT---
Always read this context silently. Never read it aloud. Use it to inform your response."""


# ── Action Tag Patterns ──────────────────────────────────────
_URL_ACTION_PATTERN = re.compile(r'\[ACTION:OPEN_URL:(.*?)\]')
_REMINDER_ADD_PATTERN = re.compile(r'\[REMINDER:ADD:(.*?):(.*?):(.*?)\]')
_REMINDER_DELETE_PATTERN = re.compile(r'\[REMINDER:DELETE:(\d+)\]')
_SCHEDULE_ADD_PATTERN = re.compile(r'\[SCHEDULE:ADD:(.*?):(.*?):(.*?)\]')
_SCHEDULE_REMOVE_PATTERN = re.compile(r'\[SCHEDULE:REMOVE:(.*?):(.*?)\]')


def _build_context_block() -> str:
    """
    Builds the context string that gets appended to each user message.
    Contains current schedule, reminders, and date/time.
    """
    schedule_json = json.dumps(get_schedule(), indent=2)
    reminders_json = json.dumps(get_reminders(), indent=2)
    current_date = datetime.now().strftime("%A, %B %d, %Y — %I:%M %p")

    context = (
        f"\n\n---CONTEXT---\n"
        f"CURRENT_SCHEDULE: {schedule_json}\n"
        f"CURRENT_REMINDERS: {reminders_json}\n"
        f"CURRENT_DATE: {current_date}\n"
        f"---END CONTEXT---"
    )
    return context


def _process_action_tags(response_text: str) -> str:
    """
    Scans the response for action tags, executes them, and strips
    them from the text so they don't go to TTS.

    Returns the cleaned text.
    """
    clean_text = response_text

    # ── URL Actions ──────────────────────────────────────────
    url_matches = _URL_ACTION_PATTERN.findall(clean_text)
    for url in url_matches:
        url = url.strip()
        print(f"🌐 Opening URL: {url}")
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"   Failed to open URL: {e}")
    clean_text = _URL_ACTION_PATTERN.sub('', clean_text)

    # ── Reminder ADD Actions ─────────────────────────────────
    reminder_add_matches = _REMINDER_ADD_PATTERN.findall(clean_text)
    for task, time_str, date_str in reminder_add_matches:
        task = task.strip()
        time_str = time_str.strip()
        date_str = date_str.strip()
        print(f"📝 Adding reminder: {task} at {time_str} on {date_str}")
        add_reminder(task, time_str, date_str)
    clean_text = _REMINDER_ADD_PATTERN.sub('', clean_text)

    # ── Reminder DELETE Actions ──────────────────────────────
    reminder_del_matches = _REMINDER_DELETE_PATTERN.findall(clean_text)
    for rid in reminder_del_matches:
        rid = int(rid.strip())
        print(f"🗑  Deleting reminder ID: {rid}")
        delete_reminder(rid)
    clean_text = _REMINDER_DELETE_PATTERN.sub('', clean_text)

    # ── Schedule ADD Actions ─────────────────────────────────
    schedule_add_matches = _SCHEDULE_ADD_PATTERN.findall(clean_text)
    for day, time_str, event in schedule_add_matches:
        day = day.strip()
        time_str = time_str.strip()
        event = event.strip()
        print(f"📅 Adding schedule event: {event} on {day} at {time_str}")
        add_event(day, time_str, event)
    clean_text = _SCHEDULE_ADD_PATTERN.sub('', clean_text)

    # ── Schedule REMOVE Actions ──────────────────────────────
    schedule_rem_matches = _SCHEDULE_REMOVE_PATTERN.findall(clean_text)
    for day, time_str in schedule_rem_matches:
        day = day.strip()
        time_str = time_str.strip()
        print(f"📅 Removing schedule event on {day} at {time_str}")
        remove_event(day, time_str)
    clean_text = _SCHEDULE_REMOVE_PATTERN.sub('', clean_text)

    # Clean up extra whitespace from tag removal
    clean_text = re.sub(r'\s{2,}', ' ', clean_text).strip()

    return clean_text


def _trim_history(history: list) -> list:
    """
    Trims conversation history to the last MAX_CONVERSATION_HISTORY messages.
    """
    if len(history) > MAX_CONVERSATION_HISTORY:
        return history[-MAX_CONVERSATION_HISTORY:]
    return history


def get_response(user_text: str, history: list, status_callback=None) -> tuple:
    """
    Sends user text to GPT-4o with context and returns the response.

    Args:
        user_text: The transcribed text from the user.
        history: Conversation history as a list of message dicts.
        status_callback: Optional function(status_str) for GUI updates.

    Returns:
        Tuple of (clean_response_text, updated_history)
        clean_response_text has all action tags stripped (safe for TTS).
    """
    if status_callback:
        status_callback("Thinking...")

    # Build the user message with context injected
    context_block = _build_context_block()
    user_message_with_context = user_text + context_block

    # Add user message to history
    history.append({"role": "user", "content": user_message_with_context})

    # Trim history to prevent token overflow
    history = _trim_history(history)

    # Build the full messages array
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history
    ]

    try:
        print("🤖 Calling GPT-4o...")
        response = _client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=OPENAI_TEMPERATURE,
        )

        raw_response = response.choices[0].message.content
        print(f"💬 Jarvis (raw): {raw_response}")

        # Process action tags and get clean text for TTS
        clean_response = _process_action_tags(raw_response)

        # Add assistant response to history (store the raw version for context)
        history.append({"role": "assistant", "content": raw_response})
        history = _trim_history(history)

        return clean_response, history

    except Exception as e:
        error_msg = f"I'm having trouble connecting to my brain right now, Bro. Error: {str(e)}"
        print(f"⚠  OpenAI API Error: {e}")

        # Still add to history so the conversation doesn't break
        history.append({"role": "assistant", "content": error_msg})
        history = _trim_history(history)

        return error_msg, history


# ── Self-test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  JARVIS LLM — Quick Test")
    print("=" * 50)
    print(f"  Model     : {OPENAI_MODEL}")
    print(f"  Max Tokens: {OPENAI_MAX_TOKENS}")
    print(f"  Temp      : {OPENAI_TEMPERATURE}")
    print(f"  History   : {MAX_CONVERSATION_HISTORY} messages max")
    print()

    test_history = []
    test_input = "Hello Jarvis, how are you?"
    print(f"  Test input: \"{test_input}\"")

    try:
        response_text, updated_history = get_response(test_input, test_history)
        print(f"\n  Response: \"{response_text}\"")
        print(f"  History length: {len(updated_history)} messages")
        print("\n  ✓ LLM module is working correctly.")
    except Exception as e:
        print(f"\n  ✗ LLM test failed: {e}")
