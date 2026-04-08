# Social Media Crawler & Analytics System
> MVP - 社交媒体内容采集与分析系统

A full-stack platform for scraping, managing, and analyzing social media content across Xiaohongshu (小红书), WeChat Public Accounts (公众号), Zhihu (知乎), and Douyin (抖音).

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router) + Tailwind CSS + Shadcn UI |
| Backend | Python 3.12 + FastAPI + SQLAlchemy 2.0 |
| Database | PostgreSQL 16 + Redis 7 |
| Crawler | Playwright (async) |
| Task Queue | APScheduler + Redis |
| Infra | Docker Compose |

## Project Structure

```
├── frontend/              # Next.js admin dashboard
├── backend/               # FastAPI + crawler engine
│   ├── app/
│   │   ├── api/           # Route handlers
│   │   ├── core/          # Config, security, deps
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic (crawlers, tasks)
│   │   ├── crud/          # Database operations
│   │   └── utils/         # Helpers
│   └── alembic/           # DB migrations
├── infra/                 # Docker Compose, nginx, etc.
└── README.md
```

## Quick Start

```bash
# 1. Start infrastructure (PostgreSQL + Redis)
docker compose -f infra/docker-compose.yml up -d

# 2. Backend setup
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Update .env with your database credentials
alembic upgrade head
uvicorn app.main:app --reload

# 3. Frontend setup
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Development Status

- [x] Step 1: Project skeleton, DB schema, Docker infra
- [x] Step 2: Account & Cookie management (manual + QR scan)
- [x] Step 3: Task scheduler + Upsert engine
- [x] Step 4: Real platform crawler (Xiaohongshu)
- [x] Step 5: Analytics dashboard (Card/Table views)
- [x] Step 6: Workspace & AI hooks

## API Endpoints

### Accounts
- `GET /accounts` - List accounts
- `POST /accounts` - Create account
- `POST /accounts/xhs/qr` - Generate QR code for XHS login
- `GET /accounts/xhs/status/{session_id}` - Check login status

### Tasks
- `GET /tasks` - List tasks
- `POST /tasks` - Create task
- `POST /tasks/{id}/toggle` - Toggle task status
- `POST /tasks/{id}/execute` - Execute task immediately

### Content
- `GET /content` - List content (supports pagination, filtering, sorting)
- `GET /content/{id}` - Get content detail
- `POST /content/{id}/star` - Toggle star
- `PATCH /content/{id}/outline` - Save manual outline
- `POST /content/{id}/ai-analyze` - AI analysis (mock)

## Features

### Account Pool
- QR code login via Playwright
- Manual cookie input
- Account status monitoring

### Task Engine
- Cron-based scheduling
- Mock data fallback for non-XHS platforms
- Incremental upsert (update metrics only for existing posts)

### XHS Scraper
- Network response interception
- Smooth scrolling simulation
- Automatic cookie refresh on failure

### Data Dashboard
- Card view / Table view toggle
- Sorting by likes/comments/shares/views
- Pagination
- Star and archive content

### Workspace
- Split-pane layout (content left, workspace right)
- Image carousel
- Manual outline editor with auto-save
- AI analysis button (mock response)
