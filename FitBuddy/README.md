# FitBuddy — AI Fitness Plan Generator

FitBuddy is a FastAPI web application that generates personalized 7-day workout plans and nutrition/recovery guidance, then revises the plan from user feedback. It follows the supplied project specification: FastAPI + Jinja2 frontend, SQLite/SQLAlchemy persistence, Gemini for AI generation, and an admin/coach view.

## Architecture

```text
Browser (Jinja2 HTML/CSS/JS)
          |
          v
      FastAPI routes
       /       \
      v         v
 SQLite/ORM   Gemini service
                 |-- workout model
                 `-- fast model
```

### Project structure

```text
FitBuddy/
├── app/
│   ├── __init__.py
│   ├── __main__.py
│   ├── config.py
│   ├── crud.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── routes.py
│   ├── schemas.py
│   └── services/
│       └── gemini_service.py
├── data/                    # SQLite database is created here
├── static/
│   ├── css/style.css
│   └── js/app.js
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── result.html
│   ├── error.html
│   └── all_users.html
├── tests/
│   ├── conftest.py
│   └── test_app.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 1. VS Code setup

1. Install Python 3.11+.
2. Open the `FitBuddy` folder in VS Code.
3. Open **Terminal → New Terminal**.
4. Create a virtual environment:

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Windows CMD

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

5. Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

6. In VS Code, select the `.venv` Python interpreter when prompted, or use **Python: Select Interpreter**.

## 2. Configure Gemini

Copy `.env.example` to `.env`.

```text
GEMINI_API_KEY=your_real_key
DEMO_MODE=false
```

For a UI/database-only demo without a key, set:

```text
DEMO_MODE=true
```

The code uses Google's current `google-genai` Python SDK rather than the older `google-generativeai` package. Model names are environment-configurable so you can change them without editing Python code. The default `gemini-3.8-flash` model is currently listed as a stable Gemini API model.

## 3. Run

From the project root:

```bash
uvicorn app.main:app --reload
```

Open:

- http://127.0.0.1:8000 — FitBuddy UI
- http://127.0.0.1:8000/docs — Swagger API documentation
- http://127.0.0.1:8000/view-all-users — local admin/coach view

Alternative:

```bash
python -m app
```

## 4. Test

Run automated tests:

```bash
pytest -q
```

The test suite uses demo mode and does not require a Gemini API key. The application also has a safe local fallback when Gemini is temporarily unavailable.

You can also test the API from Swagger at `/docs`.

### API endpoints

- `GET /api/health`
- `POST /api/generate-workout`
- `POST /api/submit-feedback`
- `GET /api/users`

Example request:

```json
{
  "user_id": "FB001",
  "name": "Alex",
  "age": 25,
  "weight": 70,
  "goal": "muscle gain",
  "intensity": "medium"
}
```

## 5. How the AI layer works

- Workout generation uses the configured `WORKOUT_MODEL` and asks Gemini for structured JSON validated through a Pydantic schema.
- Nutrition/recovery advice uses the configured `FAST_MODEL` for a concise response.
- Feedback sends the stored original plan plus the user's feedback and profile back to the workout model.
- If `DEMO_MODE=true`, deterministic local responses keep the full UI/database flow runnable without an API call.

## 6. Database

SQLite is stored at `data/fitbuddy.db` by default. Tables:

- `users`: profile information
- `workout_plans`: original plan, updated plan, feedback, nutrition tip, timestamps

The original plan is retained when a feedback revision is created, matching the supplied specification.

## 7. Important production notes

This project is designed as an educational/local deployment implementation of the supplied specification. Before public deployment:

- Add real authentication and role-based authorization to `/view-all-users`, delete, and API admin operations.
- Add CSRF protection for browser forms.
- Use PostgreSQL or another production database for multi-user deployment.
- Add rate limiting and request logging.
- Validate AI output and add human-reviewed safety rules for exercise content.
- Avoid treating AI-generated fitness or nutrition guidance as medical advice.
- Keep secrets only in environment variables or a proper secret manager.


## 8. Security note for the supplied archive

The original archive contained a Gemini API key inside `.env`. Do **not** reuse that key. Because it was shared as part of the project archive, rotate/revoke it in your Google AI account and create a new key. The corrected project ships only `.env.example`, and `.env` remains ignored by Git.

## 9. Troubleshooting

For an offline demo, use `DEMO_MODE=true`. For Gemini, use `DEMO_MODE=false` with a newly generated `GEMINI_API_KEY`. With `AI_FALLBACK_TO_DEMO=true`, temporary Gemini failures fall back to deterministic local output instead of crashing the application. Set it to `false` when you specifically want Gemini errors surfaced during development.
