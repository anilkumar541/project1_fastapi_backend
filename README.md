# project1 — FastAPI Backend

REST API for user authentication built with FastAPI, SQLAlchemy (async), and PostgreSQL.

## Tech Stack

- **FastAPI** — web framework
- **SQLAlchemy + asyncpg** — async ORM with PostgreSQL
- **Alembic** — database migrations
- **python-jose** — JWT access & refresh tokens
- **passlib[bcrypt]** — password hashing
- **fastapi-mail** — email delivery for password reset
- **pydantic-settings** — environment config
- **uv** — package manager

## Features

- Register / Login / Logout
- JWT access tokens (15 min) + refresh tokens (7 days)
- Forgot password — sends reset link via email
- Reset password — single-use token (30 min expiry)
- Get current user profile
- Change password (authenticated)

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | — | Create account |
| POST | `/auth/login` | — | Login, returns tokens |
| POST | `/auth/logout` | — | Revoke refresh token |
| POST | `/auth/forgot-password` | — | Send reset email |
| POST | `/auth/reset-password` | — | Set new password via token |
| GET | `/users/me` | Bearer | Get current user |
| POST | `/users/me/password` | Bearer | Change password |

Interactive docs available at `http://127.0.0.1:8000/docs`.

## Setup

### 1. Prerequisites

- Python 3.12+
- PostgreSQL running locally
- [`uv`](https://docs.astral.sh/uv/) installed

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure environment

Copy the example and fill in your values:

```bash
cp .env.example .env
```

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/auth_db
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30

MAIL_USERNAME=you@example.com
MAIL_PASSWORD=your_smtp_password
MAIL_FROM=you@example.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
FRONTEND_URL=http://localhost:5173
```

### 4. Run migrations

```bash
uv run alembic upgrade head
```

### 5. Start the server

```bash
uv run uvicorn main:app --reload
```

Server runs at `http://127.0.0.1:8000`.

## Project Structure

```
backend/
├── main.py               # App entry point, CORS middleware
├── pyproject.toml        # Dependencies (managed by uv)
├── alembic/              # Migration scripts
└── app/
    ├── core/
    │   ├── config.py     # Pydantic settings
    │   ├── security.py   # JWT & password hashing
    │   ├── email.py      # Password reset emails
    │   └── dependencies.py # Auth dependency (get_current_user)
    ├── db/
    │   ├── session.py    # Async engine & session
    │   └── base.py       # Declarative base
    ├── models/           # SQLAlchemy ORM models
    ├── schemas/          # Pydantic request/response schemas
    └── routers/
        ├── auth.py       # /auth/* endpoints
        └── users.py      # /users/* endpoints
```
