# ChaosFaction VPS Deployment

This setup is for a Linux VPS where the FastAPI backend must capture real network traffic.

## Recommended Architecture

- `chaosfaction.xyz` points to your VPS public IP
- Nginx terminates HTTPS on ports `80/443`
- Next.js runs locally on `127.0.0.1:3000`
- FastAPI runs locally on `127.0.0.1:8000`
- The backend container uses host networking plus packet-capture capabilities so Scapy can sniff real traffic

## 1. Prepare the VPS

Assumption:
- Ubuntu 22.04 or 24.04
- Docker and Docker Compose plugin installed
- Nginx installed

Recommended packages:

```bash
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx
```

If Docker is not installed yet:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

## 2. Point the Domain

Create DNS records:

- `A` record for `chaosfaction.xyz` -> your VPS public IP
- `A` record for `www.chaosfaction.xyz` -> your VPS public IP

## 3. Upload the Project

Clone or copy this project onto the VPS, then enter the folder:

```bash
git clone <your-repo-url> chaosfaction
cd chaosfaction
```

## 4. Configure Environment

Create the VPS env file:

```bash
cp .env.vps.example .env.vps
```

Update `.env.vps`:

- keep `BACKEND_API_URL=http://127.0.0.1:8000`
- set `ALLOWED_ORIGINS` to your real domain
- set `CAPTURE_INTERFACE` to the actual server interface

Find the correct interface with:

```bash
ip -br addr
ip route | grep default
```

Common values are `eth0`, `ens3`, or `enp1s0`.

## 5. Start the Application

Build and run both services:

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml up -d --build
```

Check status:

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml ps
docker compose --env-file .env.vps -f docker-compose.vps.yml logs -f backend
docker compose --env-file .env.vps -f docker-compose.vps.yml logs -f frontend
```

Local server tests:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:3000/health
```

## 6. Configure Nginx

Copy the provided config:

```bash
sudo cp deploy/nginx/chaosfaction.xyz.conf /etc/nginx/sites-available/chaosfaction.xyz
sudo ln -s /etc/nginx/sites-available/chaosfaction.xyz /etc/nginx/sites-enabled/chaosfaction.xyz
sudo nginx -t
sudo systemctl reload nginx
```

## 7. Enable HTTPS

Issue the certificate:

```bash
sudo certbot --nginx -d chaosfaction.xyz -d www.chaosfaction.xyz
```

Then reload Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 8. Test the Live App

Open:

- `https://chaosfaction.xyz`
- `https://chaosfaction.xyz/dashboard`
- `https://chaosfaction.xyz/health`

Packet-capture smoke test:

```bash
curl -X POST "https://chaosfaction.xyz/api/packets/capture/start?count=20&timeout=5"
curl "https://chaosfaction.xyz/api/packets/"
```

## 9. Update the App Later

```bash
git pull
docker compose --env-file .env.vps -f docker-compose.vps.yml up -d --build
```

## 10. Troubleshooting

If the frontend loads but API calls fail:

- confirm `docker compose ... logs frontend`
- confirm `.env.vps` still has `BACKEND_API_URL=http://127.0.0.1:8000`
- confirm backend is healthy with `curl http://127.0.0.1:8000/health`

If packet capture fails:

- verify `CAPTURE_INTERFACE` is correct
- verify the backend container is running with `NET_ADMIN` and `NET_RAW`
- check backend logs for Scapy/libpcap errors
- confirm the VPS provider actually allows packet capture on that interface

If Nginx fails:

- run `sudo nginx -t`
- check that DNS already points to the VPS before running Certbot

## Security Notes

- This deployment uses host networking for the backend so packet capture can access the real VPS interface
- Only expose `80` and `443` publicly through the firewall
- Do not expose `3000` or `8000` to the internet unless you explicitly need that
