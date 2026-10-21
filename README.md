# ArtMind AI Portal

An AI-powered digital art gallery. Visitors can browse paintings, search in plain language, get personalized recommendations, chat with an art assistant, upload a painting to read its color palette, and keep their own collection. Administrators get a statistics dashboard and the full Django admin.

Built as an academic eProject with a React frontend and a Django REST backend. The AI parts use existing services and libraries (OpenAI and OpenCV) and every one of them has a built-in fallback, so the whole site works without any API key.

## Features

- **Gallery** with category, style, medium and color filters, sorting (newest, most viewed, trending, A to Z) and pages
- **Natural-language search**, for example "modern abstract paintings with blue colors"
- **ArtMind Assistant**, a chatbot about styles, techniques, artists, recommendations and using the site
- **Analyze Artwork**: upload a painting photo to get its real color palette and the closest paintings in the gallery
- **Recommendations** based on favorites, viewing history and saved preferences
- **My Collection**: recently viewed, favorites, favorite categories, recommendations and curated picks
- **Painting details** with an AI-written or generated summary, similar paintings, and PDF / Word download
- **Accounts**: register, log in, log out (Django sessions, hashed passwords)
- **Admin analytics** with charts, plus the Django admin for paintings, artists, categories and users
- Responsive design for phone, tablet and desktop

## Technologies

| Part | Tools |
|---|---|
| Frontend | React, Vite, React Router, Bootstrap 5, Bootstrap Icons, plain CSS |
| Backend | Python, Django, Django REST Framework, django-cors-headers |
| Database | SQLite (development) |
| AI and images | OpenAI API (optional), OpenCV, NumPy, Pillow |
| Documents | ReportLab (PDF), python-docx (Word) |

## Requirements

- Python 3.12 or newer (developed on 3.13)
- Node.js 20.19 or newer (developed on Node 24) and npm
- An OpenAI API key is **optional**. See "Configure the AI" below.

The commands below are for Windows PowerShell. On macOS or Linux, activate the virtual environment with `source venv/bin/activate` and copy the env file with `cp .env.example .env`.

## Installation

### 1. Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

If PowerShell refuses to run the activate script, run this once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Open `backend\.env` and set a secret key. You can generate one with:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Then create the database and the sample data:

```powershell
python manage.py migrate
python manage.py seed_gallery
python manage.py seed_demo
python manage.py createsuperuser
```

- `seed_gallery` loads 6 categories, 8 artists and 18 sample paintings.
- `seed_demo` creates the demo account and some activity for it.
- `createsuperuser` creates your own administrator login. There is no default admin password.

### 2. Frontend

```powershell
cd frontend
npm install
```

## Environment variables

Set these in `backend\.env`. This file is ignored by git, so secrets never get committed. `backend\.env.example` shows the format.

| Variable | Required | Meaning |
|---|---|---|
| `DJANGO_SECRET_KEY` | Yes | Django's secret key. Generate your own. |
| `DEBUG` | No | `True` for development (default). Use `False` in production. |
| `OPENAI_API_KEY` | No | Turns on the real AI features. Leave empty to use the built-in methods. |
| `OPENAI_MODEL` | No | The model to use, `gpt-4o-mini` by default. Change it if that model is retired. It must support images for image analysis. |

API keys are read only by the backend. They are never sent to the browser and never written in the source code.

## Run the project

Use **two terminals**, both left running.

**Terminal 1: backend** (the prompt must start with `(venv)`)

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py runserver
```

**Terminal 2: frontend**

```powershell
cd frontend
npm run dev
```

Open **http://localhost:5173**. The frontend forwards `/api` and `/media` requests to Django on port 8000, so both servers must be running. The Django admin is at http://127.0.0.1:8000/admin/.

## Demo accounts

| Account | Username | Password | Notes |
|---|---|---|---|
| Demo visitor | `demo` | `ArtMind#Demo2026` | Created by `seed_demo`, with favorites, history and searches. For local demos only. |
| Administrator | the one you create | the one you choose | Created with `createsuperuser`. Sees the Analytics page and the Django admin. |

## Configure the AI

Without a key, everything works using built-in methods, and the site says so wherever it matters.

| Feature | Without a key | With an OpenAI key |
|---|---|---|
| Search | Keyword matching with typo tolerance | A model reads the sentence and extracts the filters |
| Assistant | Built-in answers and gallery lookups | A model writes the answers, grounded in the gallery |
| Painting summary | Built from the painting's details | Written by a model, then saved |
| Analyze Artwork: colors | Measured with OpenCV | Measured with OpenCV |
| Analyze Artwork: category and style | A rough estimate from color similarity, labeled as a demo result | Identified by a vision model |

To turn the AI on, add your key to `backend\.env`:

```
OPENAI_API_KEY=your-key-here
```

Restart the backend. Never share the key or commit it. Requests to OpenAI are billed to your account, and uploaded images are sent to OpenAI for classification. Whenever the AI service is unavailable the app falls back to the built-in methods automatically, and the AI endpoints are rate limited.

## Run the tests

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py test
```

There are 46 automated tests (login, gallery, favorites, search, the assistant, recommendations, uploads, downloads, dashboard and permissions). They use a temporary database and temporary files and never call OpenAI. For the frontend:

```powershell
cd frontend
npm run lint
npm run build
```

## API overview

| Endpoint | Purpose |
|---|---|
| `GET /api/artworks/` | List paintings. Supports `category`, `style`, `medium`, `color`, `sort` and `page`. |
| `GET /api/artworks/<id>/` | Painting details with similar paintings. Counts a view. |
| `GET /api/artworks/<id>/summary/` | Short summary of a painting |
| `GET /api/artworks/<id>/download/pdf/` | Details as PDF. Also `docx` for Word. |
| `GET /api/categories/` | Categories with painting counts |
| `GET /api/favorites/` | Your favorites (login required) |
| `POST /api/favorites/` | Add a favorite, body `{"artwork_id": 1}` |
| `DELETE /api/favorites/<artwork_id>/` | Remove a favorite |
| `GET /api/recommendations/` | Recommended For You |
| `POST /api/search/` | Natural-language search, body `{"query": "..."}` |
| `POST /api/ai/chat/` | Assistant, body `{"message": "...", "history": [...]}` |
| `POST /api/ai/analyze-image/` | Painting analysis, multipart field `image` |
| `GET /api/dashboard/` | Data for My Collection (login required) |
| `GET /api/analytics/` | Statistics (administrators only) |
| `POST /api/auth/register/` `login/` `logout/`, `GET /api/auth/me/` | Accounts |

## Project structure

```
ArtMind-AI-Portal/
├── backend/
│   ├── config/         Django settings and root URLs
│   ├── accounts/       Registration, login, user preferences
│   ├── gallery/        Artists, categories, paintings, favorites, history
│   ├── ai_services/    Search, assistant, recommendations, image analysis, summaries, downloads
│   ├── analytics/      Administrator statistics
│   └── media/          Painting images and uploads
├── frontend/
│   └── src/
│       ├── api/        One small file per group of API calls
│       ├── components/ Navbar, cards, charts, filters and other reusable parts
│       ├── context/    Login state
│       ├── pages/      Home, Gallery, Painting details, Assistant, Analyze, My Collection, Analytics
│       └── styles/     Design tokens and component styles
└── docs/               Project report, diagrams and screenshots
```

## Security notes

- Passwords are hashed by Django and never stored as plain text
- Session login with CSRF protection on every change request
- Secrets live in environment variables, never in the code or the browser
- Uploads are limited to JPG, PNG and WEBP up to 5 MB, must be real images, and are re-saved without metadata under random names
- Permissions: favorites and My Collection need a login, and analytics is for administrators only
- AI endpoints are rate limited
- Friendly error messages replace raw errors

## Known limitations

- The 18 sample paintings are generated placeholder images with fictional titles and artists. Replace them with real artworks in the Django admin.
- The built-in recommender is rule-based. It does not learn from other users.
- Without an AI key, the Analyze page can only estimate category and style, and it labels them as a demo result.
- SQLite is for development. Use a production database and server for a real deployment.
- Uploaded files are not cleaned up automatically.

## Troubleshooting

| Problem | Fix |
|---|---|
| Page says "Could not reach the API" or `ERR_CONNECTION_REFUSED` | Start the Django server. Both servers must be running. |
| `No module named ...` in the backend | The prompt is missing `(venv)`. Activate the virtual environment, then run `pip install -r requirements.txt`. |
| `database is locked` | Close other programs that have `db.sqlite3` open, and make sure only one Django server is running. |
| Vite says port 5173 is in use | Close the old frontend terminal. The port is fixed on purpose because Django trusts that address. |
| Fonts look plain | The fonts load from Google Fonts, so an internet connection is needed. |
| Odd file errors or very slow installs | Keep the project outside OneDrive, for example in `C:\Dev`. |

## Screenshots

Add screenshots of the main pages to `docs/screenshots/` (home, gallery, painting details, assistant, analyze, my collection, analytics).