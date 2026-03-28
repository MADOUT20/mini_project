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
KNOWN_MALICIOUS_DOMAINS=
KNOWN_MALICIOUS_IPS=
```

### Watched Site Detection

The backend can treat watched bad domains and watched bad destination IPs as first-class threats when you provide real indicators.

- `MALICIOUS_SITE_VISIT` is raised when packet capture sees a watched site through DNS, a browser host indicator, or a resolved destination IP.
- `MALICIOUS_DESTINATION` is raised when outbound traffic hits an IP in `KNOWN_MALICIOUS_IPS`.
- Leave those lists empty if you only want behavior-based detection.
- Add watched sites in `backend/.env` using `domain` or `domain=SEVERITY`.

Example:
```bash
KNOWN_MALICIOUS_DOMAINS=tlauncher.org=HIGH,some-risky-site.example=CRITICAL
```

Notes:
- A host or DNS match keeps the configured severity.
- An IP-only match is still useful, but it is treated as slightly lower confidence because shared hosting and CDNs can reuse the same IP.

For a macOS live packet-capture test:

1. Start capture mode:
```bash
./scripts/dev-local-capture.sh
```
2. Open `http://localhost:3000/dashboard`
3. Start a longer capture:
```bash
curl -X POST "http://localhost:8000/api/packets/capture/start?count=200&timeout=15"
```
4. Open or hard-reload the watched site during the capture window.

The dashboard will only raise `MALICIOUS_SITE_VISIT` if you have added real watched domains to `backend/.env`. Otherwise it will focus on behavior-based findings such as scans, suspicious DNS, beaconing, and exfiltration.

### Mobile Testing

The intended flow is:
- your Mac runs the dashboard and monitoring backend
- your phone is only a client using the local proxy
- the phone does not need to open the dashboard

1. Start capture mode:
```bash
./scripts/dev-local-capture.sh
```
2. Look for the printed proxy address such as `192.168.0.101:8888`
3. On your phone, use the Wi-Fi proxy settings:
   `Wi-Fi -> your network -> Configure Proxy -> Manual`
4. Set `Server` to your Mac LAN IP and `Port` to `8888`
5. Visit a watched site on the phone while the Mac dashboard stays open locally

Important:
- The phone does not need dashboard access.
- The local proxy mode is the easiest way to route phone website traffic through the backend without reconfiguring your whole network.
- HTTPS websites still work in proxy mode because the proxy records the destination host from the CONNECT request and tunnels the traffic through unchanged.

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
