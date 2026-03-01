# ChaosFaction - Network Security Dashboard

A full-stack security monitoring dashboard with real-time packet inspection, threat detection, and traffic analysis.

## 🏗️ Project Structure

```
project-root/
├── frontend/          # Next.js + React UI (Deployed on Vercel)
├── backend/           # FastAPI backend (Deploy on Railway/Render/AWS)
└── docker-compose.yml # Local development
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ & pnpm
- Python 3.11+
- Docker (optional)

### Local Development

**Option 1: Without Docker**

**Frontend:**
```bash
cd frontend
pnpm install
pnpm dev
# http://localhost:3000
```

**Backend (in another terminal):**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# http://localhost:8000
```

**Option 2: With Docker**
```bash
docker-compose up
```

### Environment Variables

Copy `.env.example` to `.env.local` and update values:

```bash
# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Backend
BACKEND_PORT=8000
```

## 📦 Deployment

### Frontend (Vercel)
- Already deployed at: https://chaosfaction.xyz/
- Set `NEXT_PUBLIC_API_URL` environment variable in Vercel dashboard

### Backend (Railway/Render/AWS)
1. Push backend folder to a Git repo
2. Connect to Railway/Render
3. Set environment variables
4. Deploy

## 🔌 API Endpoints

- `GET /api/traffic` - Traffic statistics
- `GET /api/threats` - Threat detection data
- `GET /api/packets` - Packet inspection data
- `GET /admin/` - Admin panel data

## 📝 Frontend API Integration

Update your components to call the backend:

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL;

const fetchTraffic = async () => {
  const res = await fetch(`${API_URL}/api/traffic`);
  return res.json();
};
```

## 🛠️ Tech Stack

**Frontend:**
- Next.js 16+
- React 19
- Tailwind CSS
- Shadcn/ui

**Backend:**
- FastAPI
- Uvicorn
- Pydantic

## 📚 Additional Resources

- [Next.js Docs](https://nextjs.org/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Docker Docs](https://docs.docker.com)
