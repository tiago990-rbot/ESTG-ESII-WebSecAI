from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import token_secret, value
from app.core.deployment import validate_deployment
from app.db.migrate import upgrade_schema
from app.services.investigation_service import recover_interrupted
from app.api.routes import auth, scans, users, investigations, quotas, lab

@asynccontextmanager
async def lifespan(app):
    token_secret()
    validate_deployment()
    upgrade_schema()
    recover_interrupted()
    from app.services.lab_service import recover
    recover()
    yield

app = FastAPI(title="WebSecAI API", description="Postura técnica, Threat Intelligence e OSINT com evidências.", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=value("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","), allow_credentials=True, allow_methods=["GET", "POST", "DELETE"], allow_headers=["Authorization", "Content-Type"])
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(scans.router)
app.include_router(investigations.router)
app.include_router(quotas.router)
app.include_router(lab.router)
from app.core.lab_body_limit import LabBodyLimit
app.add_middleware(LabBodyLimit)
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from starlette.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def safe_lab_validation(request,exc):
    if request.url.path.startswith(('/api/v1/lab','/api/v1/usage')):
        return JSONResponse(status_code=422,content={'detail':'Dados inválidos ou acima dos limites. Os valores submetidos não são devolvidos na mensagem de erro.'})
    return await request_validation_exception_handler(request,exc)

@app.get("/")
def root():
    return {"message": "WebSecAI API", "version": "2.0.0", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}
