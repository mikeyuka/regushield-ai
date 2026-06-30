# ReguShield AI - Production Deployment Guide

This guide outlines the steps to deploy the ReguShield AI Backend and Celery Worker to production using Render or Railway.

## Prerequisites
- A GitHub repository containing the project code.
- Accounts on [Render](https://render.com) or [Railway](https://railway.app).

## 1. Database & Redis Setup
- **PostgreSQL**: Provision a managed PostgreSQL instance.
- **Redis**: Provision a managed Redis instance.

## 2. Environment Variables
Configure the following environment variables in your hosting provider's dashboard:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (e.g., `postgresql://user:pass@host:port/db`) |
| `REDIS_URL` | Redis connection string (e.g., `redis://host:port/0`) |
| `ANTHROPIC_API_KEY` | Your Anthropic API Key for Claude 3.5 Sonnet |
| `STRIPE_SECRET_KEY` | Stripe Secret Key for payments |
| `GOCARDLESS_ACCESS_TOKEN` | GoCardless Access Token for billing |
| `PYTHONPATH` | `/app` |

## 3. Deploying to Render

### Backend API (Web Service)
1. **Connect Repo**: Select your project repository.
2. **Environment**: `Docker`.
3. **Plan**: Select a plan (Standard or higher recommended for production).
4. **Environment Variables**: Add the variables from step 2.
5. **Auto-Deploy**: Enabled.
6. **Service URL**: `https://regushield-api-v2-python.onrender.com`

### Celery Worker (Background Worker)
1. **Service Type**: `Background Worker`.
2. **Command**: `celery -A app.worker.celery_app worker --loglevel=info`.
3. **Environment**: `Docker`.
4. **Environment Variables**: Same as the API.

## 4. Deploying to Railway

1. **New Project**: Select "Deploy from GitHub repo".
2. **Add Services**:
   - Add a **PostgreSQL** database.
   - Add a **Redis** instance.
3. **Configure Backend**:
   - Railway will detect the `Dockerfile` in `backend/`.
   - Set the start command to `uvicorn app.main:app --host 0.0.0.0 --port ${PORT}`.
4. **Configure Worker**:
   - Add another service from the same repo.
   - Set the start command to `celery -A app.worker.celery_app worker --loglevel=info`.
5. **Variables**: Use Railway's `${{Postgres.DATABASE_URL}}` and `${{Redis.REDIS_URL}}` references.

## 5. Verification
Once deployed, verify the health status:
- API: `https://regushield-api-mike-v2.onrender.com/health`
- Expected Response: `{"status": "healthy", "service": "ReguShield AI", "database": "connected"}`

## 6. Deploying the Frontend (Vercel/Netlify)

### Vercel Deployment
1. **Connect Repo**: Select your project repository.
2. **Framework Preset**: `Vite`.
3. **Root Directory**: `frontend/`.
4. **Environment Variables**:
   - Add `VITE_API_URL`: Set this to your deployed backend URL (e.g., `https://regushield-api-mike-v2.onrender.com`). **Note**: Do not include a trailing slash.
5. **Build & Deploy**: Click Deploy. The `vercel.json` file in the frontend folder will handle client-side routing automatically.

### Netlify Deployment
1. **New Site**: Import from GitHub.
2. **Base Directory**: `frontend/`.
3. **Build Command**: `npm run build`.
4. **Publish Directory**: `dist/`.
5. **Environment Variables**: Add `VITE_API_URL` (same as Vercel).
6. **Redirects**: Create a `frontend/public/_redirects` file with `/* /index.html 200` if routing issues occur.

## 7. Operational Alerts
Ensure the backend `WEBHOOK_URL` is configured in your cloud dashboard to receive real-time notifications for:
- Successful document validations.
- High-risk ingredient detection alerts.
- System health anomalies.
