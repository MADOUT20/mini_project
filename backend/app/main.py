import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.api.routes import (
    traffic_router, threats_router, packets_router,
    admin_router, notifications_router, health_router, users_router, proxy_service
)

app = FastAPI(
    title="ChaosFaction API",
    description="Network Security Monitoring API",
    version="1.0.0"
)

# CORS middleware
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(traffic_router)
app.include_router(threats_router)
app.include_router(packets_router)
app.include_router(admin_router)
app.include_router(notifications_router)
app.include_router(users_router)


@app.on_event("startup")
async def startup_event():
    proxy_enabled = os.getenv("PROXY_ENABLED", "0").lower() in {"1", "true", "yes", "on"}
    if not proxy_enabled:
        return

    proxy_host = os.getenv("PROXY_HOST", "0.0.0.0")
    proxy_port = int(os.getenv("PROXY_PORT", "8888"))
    await proxy_service.start(host=proxy_host, port=proxy_port)


@app.on_event("shutdown")
async def shutdown_event():
    await proxy_service.stop()

@app.get("/")
async def root():
    return {
        "message": "ChaosFaction API",
        "docs": "/docs",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
