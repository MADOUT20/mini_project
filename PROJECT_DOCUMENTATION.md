# ChaosFaction - Project Documentation

**Project:** Network Security Dashboard  
**Status:** Live at https://chaosfaction.xyz/  
**Date:** March 1, 2026

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Quick Start](#quick-start)
3. [Folder Descriptions](#folder-descriptions)
4. [API Endpoints](#api-endpoints)
5. [Deployment](#deployment)

---

## Project Structure

```
project-root/
│
├── frontend/                 # Next.js UI (Deployed on Vercel)
│   ├── app/                 # Pages & routes
│   ├── components/          # React components
│   │   ├── dashboard/       # Dashboard UI
│   │   └── ui/              # Reusable UI library
│   ├── hooks/               # Custom React hooks
│   ├── lib/                 # Utilities
│   └── package.json
│
├── backend/                  # FastAPI (Deploy on Railway/Render)
│   ├── app/
│   │   ├── main.py         # Entry point
│   │   ├── api/            # Route handlers
│   │   ├── models/         # Data schemas
│   │   ├── services/       # Business logic
│   │   └── ml/             # ML models
│   └── requirements.txt
│
├── scripts/                 # Local setup/run helpers
└── README.md
```

---

## Quick Start

### Local Development

**Recommended setup:**
```bash
./scripts/setup-local.sh
./scripts/dev-local.sh
```

**Manual backend run:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
→ http://localhost:8000

**Terminal 2 - Frontend:**
```bash
cd frontend
pnpm install
pnpm dev
```
→ http://localhost:3000

---

## Folder Descriptions

### Frontend (`/frontend`)

- **`app/`** - Next.js pages (landing, dashboard, login, etc)
- **`components/dashboard/`** - Dashboard UI (charts, threats, packets, etc)
- **`components/ui/`** - Shadcn/UI components (buttons, cards, modals, etc)
- **`hooks/`** - Custom hooks (toast notifications, mobile detection)
- **`lib/`** - Utility functions

### Backend (`/backend`)

- **`api/`** - REST endpoints
  - `traffic.py` - Network traffic data
  - `threats.py` - Threat detection & response
  - `packets.py` - Packet capture & inspection
  - `admin.py` - Admin settings

- **`models/`** - Request/response schemas
- **`services/`** - Business logic (packet processing, threat detection)
- **`ml/`** - ML models for threat detection

---

## How to Use

### Add a New Page
```bash
# Create in frontend/app/
touch frontend/app/new-page/page.tsx
```

### Add a New API Endpoint
```python
# Create in backend/app/api/
# backend/app/api/new_feature.py

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["feature"])

@router.get("/new-endpoint")
async def get_data():
    return {"data": "your data"}
```

Then add to `backend/app/main.py`:
```python
from .api import new_feature
app.include_router(new_feature.router)
```

### Call API from Frontend
```typescript
const response = await fetch(
  `${process.env.NEXT_PUBLIC_API_URL}/api/new-endpoint`
);
const data = await response.json();
```

---

## API Endpoints

### Traffic
```
GET /api/traffic
  → Returns traffic statistics (packets, bytes, protocols)

GET /api/traffic/history
  → Returns traffic over time for charts
```

### Threats
```
GET /api/threats
  → Get detected threats (severity, status)

POST /api/threats/{threat_id}/respond
  → Take action (block, alert, ignore)

POST /api/threats/analyze
  → ML analysis on packet data
```

### Packets
```
GET /api/packets
  → Get captured packets

POST /api/packets/analyze
  → Deep packet inspection

POST /api/packets/capture/start
  → Start capturing

POST /api/packets/capture/stop
  → Stop capturing
```

### Admin
```
GET /admin/dashboard
  → Admin overview

GET /admin/settings
  → System settings

PUT /admin/settings
  → Update settings

GET /admin/users
  → List users
```

---

## ML Integration

### Add a ML Model

**1. Train & Save Model:**
```python
import pickle
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

pickle.dump(model, open("backend/app/ml/models/threat_model.pkl", "wb"))
```

**2. Load in Backend:**
```python
# backend/app/ml/threat_model.py
import pickle

class ThreatModel:
    def __init__(self):
        self.model = pickle.load(open("models/threat_model.pkl", "rb"))
    
    def predict(self, features):
        return self.model.predict_proba([features])[0][1]

threat_model = ThreatModel()
```

**3. Use in API:**
```python
# backend/app/api/threats.py
from ..ml.threat_model import threat_model

@router.post("/threats/analyze")
async def analyze(packet_data: dict):
    threat_score = threat_model.predict(packet_data)
    return {"is_threat": threat_score > 0.7, "score": threat_score}
```

---

## Deployment

### Frontend (Already Live!)
- **Site:** https://chaosfaction.xyz/
- **Platform:** Vercel
- **Auto-deploys** on git push

### Backend (Manual Setup Required)

#### Option 1: Railway.app
1. Go to https://railway.app
2. Import project from GitHub
3. Set env variables: `BACKEND_PORT=8000`
4. Deploy

#### Option 2: Render.com
1. Go to https://render.com
2. Create Web Service
3. Root dir: `backend`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Update Frontend API URL
After backend is deployed, update Vercel env:
```
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

---

## Environment Variables

Create `.env.local` in both folders:

**Frontend (.env.local):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Backend (.env.local):**
```
BACKEND_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000
```

---

## Technology Stack

| Component | Tech |
|-----------|------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11 |
| UI Library | Shadcn/UI |
| ML | Scikit-learn |
| Deployment | Vercel, Railway/Render |

---

## Commands

```bash
# Frontend
pnpm install
pnpm dev
pnpm build
pnpm lint

# Backend
pip install -r requirements.txt
uvicorn app.main:app --reload
python -m pytest
```

---

## Next Steps

1. ✅ Frontend running at localhost:3000
2. ✅ Backend running at localhost:8000
3. Deploy backend to Railway/Render
4. Update `NEXT_PUBLIC_API_URL` in Vercel
5. Add more ML models as needed

---

**Questions?** Check `http://localhost:8000/docs` for interactive API documentation.
