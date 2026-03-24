# ChaosFaction - Network Security Dashboard

A full-stack security monitoring dashboard with real-time packet inspection, threat detection, and traffic analysis.

## 🏗️ Project Structure

```
project-root/
├── frontend/          # Next.js + React UI (Deployed on Vercel)
├── backend/           # FastAPI backend (Deploy on Railway/Render/AWS)
├── scripts/           # Local setup and run helpers
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- npm or pnpm

### Local Development

**macOS / Linux**
```bash
./scripts/setup-local.sh
./scripts/dev-local.sh
```

This will start:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

You can also run a quick dependency check without starting the app:
```bash
./scripts/dev-local.sh --check
```

If you want packet capture on macOS, use:
```bash
./scripts/dev-local-capture.sh
```

Note: native packet capture on macOS needs admin permissions because Scapy must access `/dev/bpf*`.

**Windows PowerShell**
```powershell
.\scripts\setup-local.ps1
.\scripts\dev-local.ps1
```

Quick dependency check:
```powershell
.\scripts\dev-local.ps1 -Check
```

If you want packet capture on Windows:
```powershell
.\scripts\dev-local-capture.ps1
```

Notes for Windows:
- the PowerShell scripts open separate backend and frontend windows
- install `Npcap` before trying live packet capture
- run capture mode so the backend starts with Administrator access

### Environment Variables

`./scripts/setup-local.sh` creates local env files for you if they do not exist yet.
The defaults are:

```bash
# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
BACKEND_API_URL=http://localhost:8000

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000
```

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
