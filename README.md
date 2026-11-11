# IOT-glasses: Smart Glasses for visually impaired users

Press a button, and the glasses take a photo of what is in front of you. An LLM turns the photo into a short description, and a speaker reads it out loud.
A carer can log in to a web dashboard to see the latest image, what the LLM said, and readings from the glasses' sensors.
Stretch goal: use distance (time-of-flight) sensors to warn about nearby obstacles and predict collisions.

DkIT Software Development, IoT I-CA. Platform: **Raspberry Pi 4**.

## Repo layout

| Folder | What's in it |
|---|---|
| `server/` | FastAPI web app: login, dashboard, and the `/api/capture` endpoint the Pi calls |
| `pi/` | Scripts that run on the Raspberry Pi, plus [WIRING.md](pi/WIRING.md) |
| `docs/` | [Architecture](docs/architecture.md) |

## Run the server (on your PC)

```bash
cd server
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # then fill it in (Linux/Mac: cp)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 and log in with the username and password from `.env`.

### Choosing the LLM

- **None (image only):** set `LLM_BACKEND=none`. The Pi's photo shows up on the dashboard, and no description is generated.
- **Free, local:** install a vision model in LM Studio (for example Gemma 3 4B or Qwen2.5-VL 7B), then start its local server (Developer tab → Start server).
  Set `LLM_BACKEND=local` and `LOCAL_LLM_MODEL` to the model name LM Studio shows.
- **Claude API:** set `LLM_BACKEND=claude` and `ANTHROPIC_API_KEY`. You pay per photo. `CLAUDE_MODEL` defaults to `claude-opus-5-5`; `claude-haiku-5-5` is much cheaper.

## Run on the Pi

See [pi/WIRING.md](pi/WIRING.md) for wiring and setup. Then:

```bash
python speak.py "Hello"                          # test the speaker
python distance_alert.py                         # live distance + LED alert
python dht_monitor.py                            # temperature and humidity
python capture_and_describe.py --image test.jpg  # full flow with a saved photo
```

## Security notes

- Secrets live in `.env` files, which are git-ignored. Never commit keys.
- The dashboard and its APIs need a login. The device endpoint needs a secret device token.
- The interactive API docs (`/docs`) are turned off.
