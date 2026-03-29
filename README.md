# 🤖 J.A.R.V.I.S. — Voice-First AI Desktop Assistant

![JARVIS Banner](file:///C:/Users/hp/.gemini/antigravity/brain/ffcf0d52-354f-44ba-9266-64f66eeaea34/jarvis_banner_1774790273763.png)

> **Just A Rather Very Intelligent System**
> *Multi-Brain (GPT-4o / Claude / Gemini) + Murf Falcon TTS + Python*

JARVIS is a premium, voice-first AI desktop assistant inspired by the iconic Iron Man interface. It acts as a personal agent on your computer, managing your life through voice commands with professional, calm, and slightly sarcastic wit.

---

## ✨ Key Features

- **🧠 Multi-Provider Support** — Switch between OpenAI (GPT-4o), Anthropic (Claude Sonnet), or Google (Gemini) as your AI "brain".
- **🎙️ Natural Voice Interaction** — Uses **Murf Falcon TTS (GEN2)** for human-like spoken responses. No robotic voices here.
- **📅 Schedule Awareness** — Fully aware of your weekly calendar. It detects conflicts and manages your time intelligently.
- **📝 Task & Reminder Management** — Set, list, and delete reminders by voice. Jarvis remembers everything.
- **📧 Smart Reply Drafting** — Drafts professional email replies to meeting invites for your verbal approval.
- **🌐 Browser Automation** — "Open YouTube" or "Search for Python tutorials" → executes instantly in your default browser.
- **🇮🇳 Bilingual Fluency** — Naturally understands and responds in both English and Hindi (Hinglish).
- **💅 Premium Dark GUI** — A sleek, translucent tkinter interface with a live conversation log and auto-refreshing schedule.

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Language** | Python 3.10+ |
| **Brain Options** | OpenAI GPT-4o / Claude 3.7 Sonnet / Gemini 2.0 Flash |
| **Voice Engine** | Murf Falcon TTS (Primary API) / pyttsx3 (Offline Fallback) |
| **Speech Input** | SpeechRecognition (Google STT Engine) |
| **Audio** | Pygame Mixer (High-Fidelity Playback) |
| **UI** | Custom Tkinter Dark Theme |

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+** installed.
- A functional **Microphone**.
- **Internet connection** (required for LLM & Murf TTS).

### 2. Installation
Clone the repository and install dependencies:

```bash
# Install the core packages
pip install -r requirements.txt
```

> [!TIP]
> **Windows Users:** If `pyaudio` fails to install, try:
> `pip install pipwin && pipwin install pyaudio`

### 3. Smart Setup (No config editing needed!)
Simply run JARVIS. If it's your first time, a **Premium Setup Dialog** will appear automatically to help you:
1. Select your preferred AI Provider.
2. Enter your API Key.
3. Configure your Murf TTS Key (optional).

```bash
python main.py
```

To switch providers or keys later, use:
```bash
python main.py --setup
```

---

## 🏗️ Project Structure

```text
jarvis/
├── main.py               ← Entry point & setup handler
├── config.py             ← Multi-provider config loader
├── core/
│   ├── agent.py          ← Core execution logic (The Brain)
│   ├── llm.py            ← Multi-provider API bridges (OpenAI/Claude/Gemini)
│   ├── stt.py            ← Speech recognition engine
│   └── tts.py            ← Murf / Pyttsx3 voice output
├── ui/
│   ├── setup_dialog.py   ← Premium first-launch configuration
│   └── gui.py            ← Main JARVIS interface
├── data/
│   ├── schedule.py       ← Your weekly calendar store
│   └── reminders.py      ← Persistent reminder management
└── .env                  ← Auto-generated API key storage
```

---

## 🗣️ Common Voice Commands

| Action | Example Phrase |
| :--- | :--- |
| **Information** | *"Jarvis, explain quantum computing like I'm five."* |
| **Reminders** | *"Remind me to call the lead developer at 5 PM."* |
| **Schedules** | *"What's on my agenda for Monday afternoon?"* |
| **Conflicts** | *"I've got a meeting this Tuesday at 10 AM, check if I'm free."* |
| **Emails** | *"Draft a polite decline for the marketing meeting."* |
| **Browser** | *"Search for nearby coffee shops" or "Open GitHub."* |
| **Exit** | *"Goodbye, Jarvis. Shutdown."* |

---

## 🔧 Troubleshooting

- **Missing Key Error:** Ensure you've completed the `--setup` or check your `.env` file for typos.
- **Audio Playback Failure:** Ensure `pygame-ce` is installed and your default audio output is correct.
- **Microphone Not Found:** Run `python main.py --test` to perform a hardware diagnostic.
- **Murf 401 Error:** Your Murf API key is invalid or has expired credits.

---

*Built with ❤ for a futuristic desktop experience.*
