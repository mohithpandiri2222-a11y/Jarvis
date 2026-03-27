# J.A.R.V.I.S. — Voice-First AI Desktop Assistant

> **Just A Rather Very Intelligent System**
> Powered by GPT-4o + Murf Falcon TTS + Python

A voice-first AI desktop assistant inspired by Iron Man's Jarvis. Speak to it, and it speaks back with a natural human-like voice. It manages your schedule, sets reminders, detects conflicts, drafts replies, and opens websites — all through voice.

---

## Features

- **Voice Conversation** — Ask anything. Jarvis answers concisely in natural speech.
- **Schedule Awareness** — Knows your weekly calendar. Detects conflicts instantly.
- **Reminder Management** — Set, list, and delete reminders by voice.
- **Smart Reply Drafting** — Drafts professional accept/decline emails for your approval.
- **Browser Commands** — "Open YouTube" / "Search for machine learning" → opens in browser.
- **Bilingual Support** — Speak in English or Hindi; Jarvis responds naturally.
- **Premium GUI** — Dark-themed tkinter interface with live chat log and schedule panel.

---

## Tech Stack

| Component         | Technology                          |
|-------------------|-------------------------------------|
| Language          | Python 3.10+                        |
| AI Brain          | OpenAI GPT-4o                       |
| Voice Output      | Murf Falcon TTS (GEN2 model)        |
| Voice Input       | Google STT via SpeechRecognition    |
| Audio Playback    | pygame                              |
| Fallback TTS      | pyttsx3 (offline)                   |
| GUI               | tkinter (dark theme)                |

---

## Setup Instructions

### 1. Prerequisites
- **Python 3.10 or higher** installed
- A working **microphone**
- **Internet connection** (for APIs)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**⚠ PyAudio on Windows:** If `pip install pyaudio` fails, use:
```bash
pip install pipwin
pipwin install pyaudio
```

### 3. Configure API Keys

Open the `.env` file in the project root and replace the placeholder values:

```env
OPENAI_API_KEY=sk-your-actual-openai-key
MURF_API_KEY=ap-your-actual-murf-key
MURF_VOICE_ID=en-IN-isha
```

**Where to get keys:**
- **OpenAI:** [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Murf:** [murf.ai/resources/api](https://murf.ai/resources/api)

### 4. Run JARVIS

**With GUI (recommended):**
```bash
python main.py
```

**Terminal-only mode:**
```bash
python main.py --no-gui
```

**Run module tests:**
```bash
python main.py --test
```

---

## Project Structure

```
jarvis/
├── main.py               ← Entry point
├── config.py             ← API key loader & validator
├── .env                  ← Your secret API keys
├── requirements.txt      ← Python dependencies
├── core/
│   ├── stt.py            ← Speech-to-Text (microphone → text)
│   ├── llm.py            ← GPT-4o API (text → AI response)
│   ├── tts.py            ← Murf Falcon TTS (text → voice)
│   └── agent.py          ← Main loop (STT → LLM → TTS)
├── data/
│   ├── schedule.py       ← Mock weekly schedule
│   └── reminders.py      ← In-memory reminder store
├── ui/
│   └── gui.py            ← Dark-themed tkinter GUI
└── audio/                ← Temp audio files (auto-created)
```

---

## Demo Script (3 minutes)

Use this exact sequence when presenting:

1. **Start** → Jarvis greets: *"Good to have you back, Bro."*
2. **Ask a question:** *"Jarvis, explain machine learning in simple terms."*
3. **Set a reminder:** *"Jarvis, remind me to submit my assignment at nine PM."*
4. **Check schedule:** *"Jarvis, what does my week look like?"*
5. **Conflict detection:** *"Jarvis, I got a meeting invite for Monday at three PM."*
   → Jarvis detects the Project Review conflict and offers to draft a decline.
6. **Draft reply:** *"Yes, draft a decline."*
   → Jarvis reads the draft aloud for approval.
7. **Browser command:** *"Jarvis, open YouTube."*
   → YouTube opens in the browser.

---

## Voice Commands

| Say This                                    | Jarvis Does This                         |
|---------------------------------------------|------------------------------------------|
| "What is machine learning?"                 | Answers the question conversationally    |
| "Remind me to call Rahul at 7 PM"           | Creates a reminder                       |
| "What's on my schedule today?"              | Reads today's schedule                   |
| "I got an invite for Monday at 3 PM"        | Checks for conflicts                     |
| "Draft a decline"                           | Generates a polite decline email         |
| "Open YouTube" / "Search for Python"        | Opens URL in browser                     |
| "Exit" / "Goodbye" / "Shutdown"             | Shuts down gracefully                    |

---

## Troubleshooting

| Error                          | Fix                                                    |
|--------------------------------|--------------------------------------------------------|
| `No module named pyaudio`      | `pip install pipwin && pipwin install pyaudio`          |
| `Could not understand audio`   | Speak clearly, reduce background noise                 |
| Murf API 401 Unauthorized      | Check MURF_API_KEY in `.env`                           |
| Murf API 400 Bad Request       | Check MURF_VOICE_ID spelling                           |
| GPT-4o 429 Too Many Requests   | Add credits at platform.openai.com/billing             |
| Audio cuts off                 | Ensure pygame busy-wait loop is working                |

---

## Available Murf Voices

| Voice ID         | Language       | Gender  |
|------------------|----------------|---------|
| `en-IN-isha`     | Indian English | Female  |
| `en-US-natalie`  | US English     | Female  |
| `en-US-marcus`   | US English     | Male    |

Change the voice in `.env`:
```env
MURF_VOICE_ID=en-US-marcus
```

---

## License

This project is for educational and demonstration purposes.

---

*Built with ❤ using GPT-4o, Murf Falcon TTS, and Python.*
