from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.core.security import get_current_user
from app.models.user import User
from app.services import quotas
from app.services.privacy import redact

router = APIRouter(prefix="/api/v1/usage",tags=["usage"])

class GrantRequest(BaseModel):
    provider: str = Field(max_length=40)
    period: str = Field(max_length=20)
    reason: str = Field(min_length=8,max_length=300)
    request_id: UUID

@router.get("")
def overview(user: User = Depends(get_current_user)):
    return quotas.dashboard(user)

@router.post("/grants",status_code=201)
def authorize(data: GrantRequest,user: User = Depends(get_current_user)):
    if len(data.reason.strip())<8:raise HTTPException(422,'Indique um motivo com pelo menos oito caracteres úteis.')
    return quotas.grant(data.provider,data.period,redact(data.reason.strip()),str(data.request_id),user)

@router.post('/tavily/sync')
def sync_tavily(user:User=Depends(get_current_user)):
    return quotas.sync_tavily(user)
