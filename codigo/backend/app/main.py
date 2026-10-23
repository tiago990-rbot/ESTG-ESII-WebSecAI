from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import token_secret, value
from app.core.deployment import validate_deployment
from app.db.migrate import upgrade_schema
from app.services.investigation_service import recover_interrupted
from app.api.routes import auth, scans, users, investigations

@asynccontextmanager
async def lifespan(app):
    token_secret()
    validate_deployment()
    upgrade_schema()
    recover_interrupted()
    yield

app = FastAPI(title="WebSecAI API", description="Postura técnica, Threat Intelligence e OSINT com evidências.", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=value("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","), allow_credentials=True, allow_methods=["GET", "POST", "DELETE"], allow_headers=["Authorization", "Content-Type"])
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(scans.router)
app.include_router(investigations.router)

@app.get("/")
def root():
    return {"message": "WebSecAI API", "version": "2.0.0", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}
