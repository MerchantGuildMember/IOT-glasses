"""Smart Glasses web server.

- Dashboard (login required): shows the latest image, the LLM status and the description.
- /api/capture (device token required): the Pi uploads a photo here and gets the description back.

Run locally:  uvicorn app.main:app --host 0.0.0.0 --port 8000   (from the server/ folder)
"""

import os
import secrets
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .llm import describe_image

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")


def require_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set. Copy server/.env.example to server/.env and fill it in.")
    return value


DASHBOARD_USER = require_setting("DASHBOARD_USER")
DASHBOARD_PASSWORD = require_setting("DASHBOARD_PASSWORD")
DEVICE_TOKEN = require_setting("DEVICE_TOKEN")
SESSION_SECRET = require_setting("SESSION_SECRET")

DATA_DIR = BASE_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
LATEST_IMAGE = DATA_DIR / "latest.jpg"
ALLOWED_TYPES = {"image/jpeg", "image/png"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024

app = FastAPI(title="Smart Glasses", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, same_site="strict", max_age=8 * 3600)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# One device for now, so the state lives in memory. A database comes later.
state = {
    "status": "Waiting for a photo",
    "description": "",
    "image_version": 0,
    "updated_at": None,
}


def set_status(status: str) -> None:
    state["status"] = status
    state["updated_at"] = time.time()


def is_logged_in(request: Request) -> bool:
    return request.session.get("user") == DASHBOARD_USER


# ---------- Login ----------

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/login")
async def login(request: Request):
    form = await request.form()
    username_ok = secrets.compare_digest(str(form.get("username", "")), DASHBOARD_USER)
    password_ok = secrets.compare_digest(str(form.get("password", "")), DASHBOARD_PASSWORD)
    if username_ok and password_ok:
        request.session["user"] = DASHBOARD_USER
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": "Wrong username or password"}, status_code=401)


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


# ---------- Dashboard (login required) ----------

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not is_logged_in(request):
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(request, "index.html", {"user": DASHBOARD_USER})


@app.get("/api/state")
async def get_state(request: Request):
    if not is_logged_in(request):
        raise HTTPException(status_code=401, detail="Login required")
    return JSONResponse(state)


@app.get("/api/image")
async def get_image(request: Request):
    if not is_logged_in(request):
        raise HTTPException(status_code=401, detail="Login required")
    if not LATEST_IMAGE.exists():
        raise HTTPException(status_code=404, detail="No image yet")
    return FileResponse(LATEST_IMAGE, headers={"Cache-Control": "no-store"})


# ---------- Device API (device token required) ----------

@app.post("/api/capture")
async def capture(image: UploadFile = File(...), x_device_token: str = Header(default="")):
    if not secrets.compare_digest(x_device_token, DEVICE_TOKEN):
        raise HTTPException(status_code=401, detail="Bad device token")
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Send a JPEG or PNG")
    image_bytes = await image.read()
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image too large")

    LATEST_IMAGE.write_bytes(image_bytes)
    state["image_version"] += 1
    state["description"] = ""

    if os.getenv("LLM_BACKEND", "local").lower() == "none":
        # Image-only mode: no LLM connected yet, just show the photo on the dashboard.
        set_status("Image received (LLM not connected yet)")
        return {"description": ""}

    set_status("Sending to LLM...")

    def on_text(chunk: str) -> None:
        if state["status"] != "LLM responding...":
            set_status("LLM responding...")
        state["description"] += chunk

    try:
        description = await describe_image(image_bytes, image.content_type, on_text)
    except Exception as exc:  # show the problem on the dashboard instead of crashing
        set_status(f"LLM error: {exc}")
        raise HTTPException(status_code=502, detail="LLM request failed") from exc

    state["description"] = description
    set_status("Done")
    return {"description": description}
