# SmartInbox Free Deployment Guide: Vercel + Railway / Render

This guide walks you through deploying the complete **SmartInbox** system using 100% free tiers:
* **Frontend**: [Vercel](https://vercel.com) (Free static Angular hosting)
* **Backend**: [Railway](https://railway.app) or [Render](https://render.com) (Free cloud hosting for Spring Boot & Python)

---

## Architecture Overview

```
 [ Browser / User ]
         │
         ▼
 [ Vercel: Angular Frontend ] (https://smart-inbox.vercel.app)
         │  /api rewrites
         ▼
 [ Railway / Render: Spring Boot Backend ] (Port 8081 / HTTPS)
         │  Internal HTTP
         ▼
 [ Railway / Render: Python AI Service ] (Port 8000 / HTTPS)
```

---

## Part 1: Deploy Backend & AI Service (Railway or Render)

### Option A: Railway (Recommended — Fast & Generous Free Tier)

1. Go to [railway.app](https://railway.app) and sign in with your GitHub account (`sriharizz`).
2. Click **New Project** -> **Deploy from GitHub repo** -> Select `smart-inbox`.
3. Railway will ask you which service to deploy. You will add **2 services**:

#### Service 1: Python AI Service
* **Root Directory**: `ai-service-python`
* **Dockerfile**: Detected automatically from `ai-service-python/Dockerfile`.
* **Variables**:
  * `PORT` = `8000`
  * `GEMINI_API_KEY` = `your_gemini_api_key_here`
* Click **Deploy**. Under **Settings** -> **Networking**, click **Generate Domain** (e.g. `https://smart-inbox-ai.up.railway.app`).

#### Service 2: Spring Boot Backend
* In the same Railway project, click **+ New** -> **GitHub Repo** -> select `smart-inbox`.
* **Root Directory**: `backend-spring`
* **Dockerfile**: Detected automatically from `backend-spring/Dockerfile`.
* **Variables**:
  * `PORT` = `8081`
  * `PYTHON_AI_SERVICE_URL` = URL from Service 1 (e.g., `https://smart-inbox-ai.up.railway.app` or Railway private domain `http://ai-service.railway.internal:8000`)
  * `GEMINI_API_KEY` = `your_gemini_api_key_here`
  * `INGESTION_MODE` = `FIXTURE` (or `IMAP`)
* Click **Deploy**. Under **Settings** -> **Networking**, click **Generate Domain** (e.g. `https://smart-inbox-backend.up.railway.app`).
* Copy this backend URL!

---

### Option B: Render.com (100% Free Forever)

If you prefer Render:
1. Sign in to [render.com](https://render.com).
2. Create **New Web Service** -> Connect `sriharizz/smart-inbox`:
   * **Name**: `smartinbox-ai`
   * **Root Directory**: `ai-service-python`
   * **Runtime**: `Docker`
   * **Environment Variables**: `GEMINI_API_KEY`
3. Create a second **Web Service**:
   * **Name**: `smartinbox-backend`
   * **Root Directory**: `backend-spring`
   * **Runtime**: `Docker`
   * **Environment Variables**:
     * `PYTHON_AI_SERVICE_URL` = `https://smartinbox-ai.onrender.com`
     * `GEMINI_API_KEY` = `your_gemini_api_key`

---

## Part 2: Deploy Frontend on Vercel (100% Free)

1. Go to [vercel.com](https://vercel.com) and log in with your GitHub account.
2. Click **Add New...** -> **Project** -> Import `sriharizz/smart-inbox`.
3. In the project setup screen:
   * **Framework Preset**: `Angular`
   * **Root Directory**: Click **Edit** and choose `frontend-angular` (⚠️ Important!).
   * **Build Command**: `npm run build`
   * **Output Directory**: `dist/frontend-angular/browser`
4. Update `frontend-angular/vercel.json` with your live Railway / Render backend URL:
   ```json
   {
     "rewrites": [
       {
         "source": "/api/:path*",
         "destination": "https://your-backend-domain.up.railway.app/api/:path*"
       },
       {
         "source": "/(.*)",
         "destination": "/index.html"
       }
     ]
   }
   ```
5. Click **Deploy**!
   Vercel will build the Angular application and provide a live URL (e.g. `https://smart-inbox.vercel.app`).

---

## Part 3: Verification

1. Open your live Vercel URL.
2. The Review Queue should load all 12 benchmark clinical cases seamlessly.
3. Clicking on any case will load the document geometry, visual bounding boxes, and ICH E2B fact extraction from the live cloud backend!
