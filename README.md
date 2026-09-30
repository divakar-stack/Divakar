# PocketSmart AI

PocketSmart AI is a server-rendered budgeting assistant for home interiors, parties, and jewelry. It combines FastAPI, Jinja2, SQLite, SQLAlchemy, signed browser sessions, a local sample catalog, and optional Google Gemini recommendations. The app works without a Gemini key and labels local estimates clearly.

## Features

- Home planner with requested items, quantities, room type, and style.
- Party planner with guest count, event preferences, cost allocation, and remaining budget.
- Jewelry planner with outfit notes and optional JPG/JPEG/PNG/WEBP upload (up to 5 MB).
- Account registration, PBKDF2 password hashing, signed sessions, dashboard, and user-specific saved history.
- Gemini requests use the Google `google-genai` SDK; missing keys, request failures, timeouts, and malformed responses fall back to local deterministic recommendations.
- Upload bytes are validated and processed in memory; images are not stored in the database or on disk.

Prices and platform names are illustrative local catalog data. There are no live Amazon, Flipkart, IKEA, Swiggy, Zomato, OYO, or jewelry vendor APIs configured.

## Architecture

`main.py` builds the FastAPI app, initializes tables on startup, mounts static files, and registers route modules. `routes/` handles pages, accounts, planning, and history. `services/` contains Gemini integration, budget-aware local recommendations, and sample catalog data. `schemas.py` validates planner and account input; `models.py` maps users and recommendations to SQLite. Templates and static assets live under `templates/` and `static/`.

## Folder structure

```text
PocketSmart AI/
├── main.py, config.py, database.py, models.py, schemas.py, auth.py
├── main_context.py, requirements.txt, .env.example, README.md
├── routes/                 # account, pages, planners, history
├── services/               # Gemini and local catalog/recommendations
├── templates/              # Jinja2 pages
├── static/css/style.css
├── static/js/app.js
└── tests/test_app.py
```

## Install on Windows PowerShell

Python 3.14 is supported by the dependency versions in `requirements.txt`. From the project folder:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation in the current terminal, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

The existing workspace also contains a `venv` based on Python 3.14.6. You can use it directly without activation: `\.\venv\Scripts\python.exe` from PowerShell.

## Environment and Gemini

Create a local environment file and generate a private secret:

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put the generated value in `SECRET_KEY` in `.env`; optionally add your key to `GEMINI_API_KEY`. Never commit `.env`. For local development, `COOKIE_SECURE=false`; set it to `true` when serving over HTTPS. When `GEMINI_API_KEY` is empty, deterministic sample recommendations are used automatically.

## Database

SQLite is initialized automatically when the app starts. The default database is `pocketsmart.db` in the project directory. To use another location, set `DATABASE_URL` in `.env`, for example `sqlite:///./pocketsmart.db`. Do not delete the database if you need saved accounts or recommendation history.

## Run the application

With the virtual environment activated:

```powershell
uvicorn main:app --reload
```

Open <http://127.0.0.1:8000>. Without activation, run `\.\venv\Scripts\python.exe -m uvicorn main:app --reload`. The interactive API schema is at <http://127.0.0.1:8000/docs>; `/startup` reports app readiness and whether Gemini is configured.

## Tests

```powershell
pytest -q
```

Tests use a temporary SQLite file and do not require a Gemini key or external APIs.

## Routes

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Landing page |
| GET/POST | `/register` | Create an account |
| GET/POST | `/login` | Sign in |
| GET | `/logout` | Clear session |
| GET | `/dashboard` | Protected dashboard |
| GET | `/home-planner`, `/party-planner`, `/jewelry-planner` | Planner forms |
| POST | `/generate-home`, `/generate-party`, `/generate-jewelry` | Validate and generate plans |
| GET | `/history` | Current user's history (HTML or JSON with `Accept: application/json`) |
| GET | `/session-info`, `/session-data` | Safe current session status |
| GET | `/recommendations-details` | Current user's saved recommendations; optional `?id=` |
| GET | `/startup` | Health and Gemini configuration status |

## Troubleshooting

- **`python` is not found:** install Python 3.14, or invoke the interpreter explicitly with `\.\venv\Scripts\python.exe`.
- **Missing package/import:** activate the intended environment, then rerun `python -m pip install -r requirements.txt`.
- **Gemini reports unavailable:** verify `GEMINI_API_KEY` in `.env` and restart Uvicorn. Fallback plans remain available without it.
- **Session key warning for deployment:** set a stable private random `SECRET_KEY` and enable secure cookies behind HTTPS. Without a configured key, the app creates a temporary random key each start, so existing sessions expire on restart.
- **SQLite locked:** stop other app processes using the same database and restart the server.
- **Image rejected:** upload a valid JPG, JPEG, PNG, or WEBP file no larger than 5 MB.