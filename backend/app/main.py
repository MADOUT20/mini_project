from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import (
    traffic_router, threats_router, packets_router, 
    admin_router, notifications_router
)
import os
from dotenv import load_dotenv

load_dotenv()

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
app.include_router(traffic_router)
app.include_router(threats_router)
app.include_router(packets_router)
app.include_router(admin_router)
app.include_router(notifications_router)
async def root():
    return {
        "message": "ChaosFaction API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
