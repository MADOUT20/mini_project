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
- Docker

### Local Development

**With Docker (Recommended)**
```bash
docker-compose up --build
```
This will start both the frontend and backend services.
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

### Environment Variables

Copy `.env.example` to `.env.local` and update values if needed. The default values are set to work with the docker-compose setup.

```bash
# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
BACKEND_API_URL=http://localhost:8000

# Backend
BACKEND_PORT=8000
```

## 🖥️ VPS Deployment

For a real Linux VPS deployment that supports packet capture, use the production compose file and guide in [DEPLOY_VPS.md](/Users/siddharthchillapwar/Desktop/network%20malware%20detection%20systerm/mini_project/DEPLOY_VPS.md).

Key production files:

- [docker-compose.vps.yml](/Users/siddharthchillapwar/Desktop/network%20malware%20detection%20systerm/mini_project/docker-compose.vps.yml)
- [.env.vps.example](/Users/siddharthchillapwar/Desktop/network%20malware%20detection%20systerm/mini_project/.env.vps.example)
- [chaosfaction.xyz.conf](/Users/siddharthchillapwar/Desktop/network%20malware%20detection%20systerm/mini_project/deploy/nginx/chaosfaction.xyz.conf)

## 🔌 API Endpoints

- `GET /health` - Health check
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
- Axios

**Backend:**
- FastAPI
- Uvicorn
- Pydantic

## 📚 Additional Resources

- [Next.js Docs](https://nextjs.org/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Docker Docs](https://docs.docker.com)
