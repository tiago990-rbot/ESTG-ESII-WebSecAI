# WebSec Check — Backend

Backend em FastAPI com SQLite, autenticação por token, histórico de análises, score, comparação e relatório PDF.

## Como correr

```powershell
cd backend
py -m pip install -r requirements.txt
py -m uvicorn app.main:app --reload --port 8000
```

Abrir documentação:

```text
http://127.0.0.1:8000/docs
```
