# Daily Assistant

An AI assistant for your terminal that reads your email, keeps your checklist, and reminds you about your daily routines. It uses [Claude](https://www.anthropic.com/claude).

```
you › what's new in my inbox?
  · checking your inbox...
  · reading an email...

You have 4 unread emails:
• Sara (Acme): wants the invoice by Friday. Needs a reply.
• Bank: monthly statement is ready.
• Newsletter ×2: nothing urgent.

Want me to add "Send invoice to Sara" to your checklist, due Friday?

you › yes, and remind me to drink water every day at 10:00
  · adding to your checklist...
  · saving a routine...

Saved: "Send invoice to Sara", due Fri 09:00. Routine: drink water, daily at 10:00.
```

## What it can do

- **Read your email:** summarize your inbox, find messages, and flag what's urgent. It only reads: it can't send, delete, or move anything, and it doesn't mark messages as read.
- **Keep a checklist:** add tasks (with due times if you want), tick them off, and list what's left.
- **Remind you about routines:** for example "gym at 07:00 on weekdays". You get a desktop notification when it's time.
- **Give a daily briefing:** one command sums up your unread email, open tasks, and today's routines.

Your checklist and routines are saved on your own computer in `~/.daily-assistant/data.json`.

## Setup (about 5 minutes)

You need **Python 3.10 or newer** and an **Anthropic API key**. You can get a key at [console.anthropic.com](https://console.anthropic.com/). Using the API costs a small amount per request.

```bash
git clone https://github.com/simohamedd/daily-assistant.git
cd daily-assistant
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
```

Open `.env` in a text editor and fill in your API key and email details.

### Connecting your email

The assistant connects to your mailbox over IMAP using an **app password**. An app password is a separate password just for this app, so your real password stays private.

| Provider | IMAP_SERVER | How to get an app password |
|---|---|---|
| Gmail | `imap.gmail.com` | Turn on 2-Step Verification, then create one at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) |
| Yahoo | `imap.mail.yahoo.com` | Account Security → Generate app password |
| iCloud | `imap.mail.me.com` | [appleid.apple.com](https://appleid.apple.com) → Sign-In and Security → App-Specific Passwords |
| Other | ask your provider | Look for "IMAP" in your provider's help pages |

Outlook and Microsoft 365 accounts usually block password-based IMAP, so they may not work.

You can skip email entirely: the checklist and routines work without it.

## Using it

```bash
python -m assistant            # chat with your assistant
python -m assistant brief      # get your daily briefing
python -m assistant remind     # turn on reminders (keep this window open)
```

Things you can say in chat:

- "Any urgent emails today?"
- "Find the email from the airline and tell me my flight time"
- "Add 'call mom' to my list for tomorrow at 6pm"
- "What's left on my checklist?" / "I finished the invoice"
- "Remind me to stretch at 15:00 on weekdays"
- "Show my routines" / "Delete the gym routine"

Type `exit` to quit.

### Getting reminders automatically

Desktop reminders only appear while `python -m assistant remind` is running. Run it in a terminal window you leave open. If you're comfortable with your system's scheduler, you can also start it automatically when you log in.

A routine that you missed by more than 30 minutes is skipped for that day, so starting `remind` late doesn't flood you with old reminders.

## Settings

All settings are read from your `.env` file:

| Setting | Default | What it does |
|---|---|---|
| `ANTHROPIC_API_KEY` | (required) | Your Anthropic API key |
| `EMAIL_ADDRESS` | | Your email address |
| `EMAIL_APP_PASSWORD` | | The app password for your email |
| `IMAP_SERVER` | `imap.gmail.com` | Your provider's IMAP server |
| `IMAP_PORT` | `993` | IMAP port |
| `ASSISTANT_MODEL` | `claude-opus-5-5` | The Claude model to use |
| `ASSISTANT_EFFORT` | `medium` | How hard Claude thinks: `low` is faster and cheaper, `high` is more thorough |
| `ASSISTANT_DATA_DIR` | `~/.daily-assistant` | Where your checklist and routines are saved |

## Privacy and safety

- Your `.env` file holds your passwords and is never uploaded to GitHub, because `.gitignore` excludes it. Never share it.
- When you ask about email, the content of the messages you ask about is sent to the Anthropic API so Claude can read it.
- The assistant has no tool for sending, deleting, or changing email. It's told to treat email content as information, not instructions, so an email that says "do X" is reported to you instead of acted on.

## How it works (for developers)

| File | What's in it |
|---|---|
| `assistant/agent.py` | The agent loop: it sends the conversation to Claude, runs any tools Claude asks for, and repeats until Claude answers |
| `assistant/tools.py` | The tools Claude can use (their descriptions and the code that runs them) |
| `assistant/email_client.py` | Read-only IMAP access |
| `assistant/store.py` | The checklist and routines, saved as JSON |
| `assistant/notify.py` | Desktop notifications for macOS, Linux and Windows |
| `assistant/__main__.py` | The `chat`, `brief` and `remind` commands |

To add a new ability, add a tool definition to `TOOLS` in `tools.py` and handle it in `_run()`.

Contributions are welcome. Open an issue or a pull request.
