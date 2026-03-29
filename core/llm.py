"""
================================================================================
JARVIS — LLM Brain Module (core/llm.py)
================================================================================
The Intelligence Layer supporting OpenAI, Anthropic, and Google.

This module acts as a universal adapter between Jarvis's high-level agent logic
and the specific API protocols of the world's leading AI providers.

Responsibilities:
1. Provider Switching: Dynamic routing to OpenAI, Claude, or Gemini.
2. Context Injection: Automatically appends the user's schedule & reminders.
3. Personality Alignment: Enforces the JARVIS system prompt (Iron Man style).
4. Action Tag Extraction: Parses [ACTION:...], [REMINDER:...], etc.
================================================================================
"""

import json
import re
import webbrowser
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    LLM_PROVIDER,
    LLM_MODEL,
    OPENAI_API_KEY,
    ANTHROPIC_API_KEY,
    GEMINI_API_KEY,
    OPENAI_MAX_TOKENS,
    OPENAI_TEMPERATURE,
    MAX_CONVERSATION_HISTORY,
    PROVIDER_NAMES,
)
from data.schedule import get_schedule, add_event, remove_event
from data.reminders import get_reminders, add_reminder, delete_reminder


# ------------------------------------------------------------------------------
# API CLIENT MANAGEMENT (LAZY INITIALIZATION)
# ------------------------------------------------------------------------------
# We don't import or initialize SDKs until they are actually needed.
# This prevents crashes if a user only has one provider's library installed.
_openai_client = None
_anthropic_client = None
_gemini_client = None


def _get_openai_client():
    """Initializes the OpenAI SDK with the current API key."""
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


def _get_anthropic_client():
    """Initializes the Anthropic (Claude) SDK."""
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _anthropic_client


def _get_gemini_client():
    """Initializes the Google Gemini SDK (v1.0.0+ style)."""
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client


# ------------------------------------------------------------------------------
# THE JARVIS PERSONALITY PROMPT
# ------------------------------------------------------------------------------
# This is the 'Core Directive'. It defines how Jarvis speaks, his relationship
# with the user ('Bro'), and his persona (Iron Man film style).
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


# ------------------------------------------------------------------------------
# ACTION TAG REGEX PATTERNS
# ------------------------------------------------------------------------------
# Jarvis executes machine actions by emitting specific bracketed tags in his text.
# The code intercepts these tags BEFORE the text reaches the user's ears (TTS).

_URL_ACTION_PATTERN = re.compile(r'\[ACTION:OPEN_URL:(.*?)\]')
_REMINDER_ADD_PATTERN = re.compile(r'\[REMINDER:ADD:(.*?):(.*?):(.*?)\]')
_REMINDER_DELETE_PATTERN = re.compile(r'\[REMINDER:DELETE:(\d+)\]')
_SCHEDULE_ADD_PATTERN = re.compile(r'\[SCHEDULE:ADD:(.*?):(.*?):(.*?)\]')
_SCHEDULE_REMOVE_PATTERN = re.compile(r'\[SCHEDULE:REMOVE:(.*?):(.*?)\]')


def _build_context_block() -> str:
    """
    Constructs a JSON-formatted string of current user data.
    This is HIDDEN from the user but given to the LLM in every message 
    so Jarvis 'knows' what the user is currently doing.
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
    Detects and executes embedded action tags, then strips them from the response.
    
    Args:
        response_text: The raw LLM response containing potential tags.
        
    Returns:
        str: The 'cleaned' response ready for Text-to-Speech output.
    """
    clean_text = response_text

    # -- 1. Web Automation --
    url_matches = _URL_ACTION_PATTERN.findall(clean_text)
    for url in url_matches:
        url = url.strip()
        print(f"🌐 [AUTO] Navigation triggered: {url}")
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"   [FAIL] Browser automation error: {e}")
    clean_text = _URL_ACTION_PATTERN.sub('', clean_text)

    # -- 2. Reminder Management (ADD) --
    reminder_add_matches = _REMINDER_ADD_PATTERN.findall(clean_text)
    for task, time_str, date_str in reminder_add_matches:
        print(f"📝 [AUTO] Database Write: Added Reminder '{task}' for {time_str} ({date_str})")
        add_reminder(task.strip(), time_str.strip(), date_str.strip())
    clean_text = _REMINDER_ADD_PATTERN.sub('', clean_text)

    # -- 3. Reminder Management (DELETE) --
    reminder_del_matches = _REMINDER_DELETE_PATTERN.findall(clean_text)
    for rid in reminder_del_matches:
        print(f"🗑  [AUTO] Database Delete: Removed Reminder ID {rid}")
        delete_reminder(int(rid.strip()))
    clean_text = _REMINDER_DELETE_PATTERN.sub('', clean_text)

    # -- 4. Schedule Management (ADD) --
    schedule_add_matches = _SCHEDULE_ADD_PATTERN.findall(clean_text)
    for day, time_str, event in schedule_add_matches:
        print(f"📅 [AUTO] Schedule Update: Added '{event}' on {day} at {time_str}")
        add_event(day.strip(), time_str.strip(), event.strip())
    clean_text = _SCHEDULE_ADD_PATTERN.sub('', clean_text)

    # -- 5. Schedule Management (REMOVE) --
    schedule_rem_matches = _SCHEDULE_REMOVE_PATTERN.findall(clean_text)
    for day, time_str in schedule_rem_matches:
        print(f"📅 [AUTO] Schedule Update: Removed entry on {day} at {time_str}")
        remove_event(day.strip(), time_str.strip())
    clean_text = _SCHEDULE_REMOVE_PATTERN.sub('', clean_text)

    # Strip redundant trailing whitespace from the final TTS-bound text
    clean_text = re.sub(r'\s{2,}', ' ', clean_text).strip()
    return clean_text


def _trim_history(history: list) -> list:
    """
    Prevents conversation history from exceeding Token/Memory limits.
    Maintains the last N messages to ensure coherent continuity.
    """
    if len(history) > MAX_CONVERSATION_HISTORY:
        return history[-MAX_CONVERSATION_HISTORY:]
    return history


# ------------------------------------------------------------------------------
# PROVIDER-SPECIFIC API ADAPTERS
# ------------------------------------------------------------------------------

def _call_openai(messages: list) -> str:
    """Standard OpenAI ChatCompletion protocol."""
    client = _get_openai_client()
    print(f"🤖 [BRAIN] Dispatching request to OpenAI-API (Model: {LLM_MODEL})...")
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        max_tokens=OPENAI_MAX_TOKENS,
        temperature=OPENAI_TEMPERATURE,
    )
    return response.choices[0].message.content


def _call_claude(messages: list) -> str:
    """Anthropic Messages standard (Claude 3/3.5)."""
    client = _get_anthropic_client()
    print(f"🤖 [BRAIN] Dispatching request to Anthropic-API (Model: {LLM_MODEL})...")

    # Claude places the system instruction into a separate field.
    system_text = ""
    conversation = []
    for msg in messages:
        if msg["role"] == "system":
            system_text = msg["content"]
        else:
            conversation.append(msg)

    response = client.messages.create(
        model=LLM_MODEL,
        max_tokens=OPENAI_MAX_TOKENS,
        system=system_text,
        messages=conversation,
    )
    return response.content[0].text


def _call_gemini(messages: list) -> str:
    """Google Gemini v1/v2 SDK protocol."""
    client = _get_gemini_client()
    print(f"🤖 [BRAIN] Dispatching request to Google-API (Model: {LLM_MODEL})...")

    system_text = ""
    conversation_parts = []
    
    # Map messages to Gemini's specific role terminology
    for msg in messages:
        if msg["role"] == "system":
            system_text = msg["content"]
        else:
            role = "model" if msg["role"] == "assistant" else "user"
            conversation_parts.append({
                "role": role,
                "parts": [{"text": msg["content"]}],
            })

    from google.genai import types
    config = types.GenerateContentConfig(
        system_instruction=system_text,
        max_output_tokens=OPENAI_MAX_TOKENS,
        temperature=OPENAI_TEMPERATURE,
    )

    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=conversation_parts,
        config=config,
    )
    return response.text


# Dynamic Dispatch Table
_PROVIDER_FUNCTIONS = {
    "openai": _call_openai,
    "claude": _call_claude,
    "gemini": _call_gemini,
}


# ------------------------------------------------------------------------------
# PRIMARY PUBLIC INTERFACE
# ------------------------------------------------------------------------------

def get_response(user_text: str, history: list, status_callback=None) -> tuple:
    """
    Processes user input, queries the active AI 'brain', and executes logic.
    
    Args:
        user_text (str): Hand-transcribed user speech.
        history (list): Current session message history.
        status_callback (callable): UI hook for real-time status updates.
        
    Returns:
        tuple: (clean_spoken_text, updated_memory_history)
    """
    if status_callback:
        status_callback("Jarvis is thinking...")

    # Enrich user message with real-time context (Schedule, Reminders, Date)
    context_block = _build_context_block()
    user_payload = user_text + context_block

    # Update session memory
    history.append({"role": "user", "content": user_payload})
    history = _trim_history(history)

    # Compile final message stack for the LLM
    final_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history
    ]

    try:
        from config import LLM_PROVIDER as current_provider
        call_fn = _PROVIDER_FUNCTIONS.get(current_provider)
        
        if not call_fn:
            raise ValueError(f"Provider '{current_provider}' is not implemented in core/llm.py dispatcher.")

        # Dispatch API Call
        raw_response = call_fn(final_messages)
        print(f"💬 [BRAIN] Response received (Raw size: {len(raw_response)} chars)")

        # Execute actions and prep text for TTS
        clean_response = _process_action_tags(raw_response)

        # Store the RAW response in memory (to keep tags for future context)
        history.append({"role": "assistant", "content": raw_response})
        history = _trim_history(history)

        return clean_response, history

    except Exception as e:
        error_msg = f"I've encountered a glitch in my cognition system, Bro. Error: {str(e)}"
        print(f"⚠  [BRAIN_FAIL] Critical API error: {e}")
        
        # We append the error message to history so the flow continues gracefully.
        history.append({"role": "assistant", "content": error_msg})
        return error_msg, history


# ------------------------------------------------------------------------------
# MODULE TESTING
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    print("-" * 60)
    print(" JARVIS Intelligence Stack — Module Test")
    print("-" * 60)
    print(f"  Target Provider: {PROVIDER_NAMES.get(LLM_PROVIDER)}")
    print(f"  Target Model   : {LLM_MODEL}")
    print("-" * 60)

    test_msg = "Jarvis, identify yourself."
    print(f"  [Input] {test_msg}")
    
    res, hist = get_response(test_msg, [])
    print(f"  [Output] {res}")
    print("-" * 60)
