import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, update

from app import models
from app.api import admin, auth, quest_types, quests, server, user
from app.config import settings
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DCSS - Drone Control Simulation Server")
os.makedirs("logs", exist_ok=True)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "type": exc.__class__.__name__,
            "details": exc.detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "type": "ValidationError",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "type": exc.__class__.__name__,
            "details": str(exc),
        },
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(quest_types.router)
app.include_router(auth.router)
app.include_router(quests.router)
app.include_router(server.router)
app.include_router(admin.router)
app.include_router(user.router)

with engine.begin() as conn:
    conn.execute(
        update(models.QuestInstance)
        .where(models.QuestInstance.status == models.QuestStatus.running)
        .values(status=models.QuestStatus.aborted, completed_at=func.now())
    )


@app.get("/")
def root():
    return {"success": True, "data": {"message": "DCSS API is running"}}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.server_host, port=settings.server_port)
