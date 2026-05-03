"""
FastAPI application entry point.

- CORS for frontend at localhost:5173
- Includes auth and admin routers
- Health check at /api/health
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import admin_routes, auth_routes

# ── App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Clinical Identity Verification API",
    description="JWT-based auth backend with RBAC (Doctor / Admin) for the telemedicine platform.",
    version="1.0.0",
)

# ── CORS ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:5174",   # identity-vaas dev server (if applicable)
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────
app.include_router(auth_routes.router)
app.include_router(admin_routes.router)


# ── Health check ─────────────────────────────────────────────────────
@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": "clinical-identity-verification"}
