import os
import socket
import subprocess
import sys
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.auth import get_current_user
from app.config import settings
from app.database import get_db

router = APIRouter(prefix="/quest", tags=["quests"])

used_ports = set()
quest_ports = {}
running_evaluators = {}


def find_free_port(start: int, end: int) -> int:
    """Возвращает свободный TCP-порт из диапазона и резервирует его."""
    for port in range(start, end + 1):
        if port in used_ports:
            continue
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                used_ports.add(port)
                return port
    raise RuntimeError(f"No free ports available in range {start}-{end}")


def release_ports(quest_guid: str) -> None:
    """Освобождает порты, зарезервированные для задания."""
    for port in quest_ports.pop(quest_guid, []):
        used_ports.discard(port)


def stop_evaluator_process(quest_guid: str) -> None:
    proc = running_evaluators.get(quest_guid)
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    running_evaluators.pop(quest_guid, None)


@router.post("/start", response_model=dict)
async def start_quest(
    request: schemas.QuestStartRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    quest_type = crud.get_quest_type(db, request.type_id)
    if not quest_type:
        raise HTTPException(status_code=404, detail="Quest type not found")

    active_count = db.query(models.QuestInstance).filter(
        models.QuestInstance.status == models.QuestStatus.running
    ).count()
    if active_count >= settings.max_quest:
        raise HTTPException(status_code=409, detail="Maximum number of running quests reached")

    sitl_port = find_free_port(settings.sitl_port_start, settings.sitl_port_end)
    proxy_port = find_free_port(settings.proxy_port_start, settings.proxy_port_end)

    quest_guid = str(uuid.uuid4())
    quest_ports[quest_guid] = [sitl_port, proxy_port]
    link = f"tcp:{settings.mavlink_public_host}:{proxy_port}"

    new_instance = models.QuestInstance(
        guid=quest_guid,
        type_id=request.type_id,
        user_id=current_user.id,
        status=models.QuestStatus.pending,
        max_time_sec=quest_type.max_time_sec,
        link=link,
    )
    db.add(new_instance)
    db.commit()
    db.refresh(new_instance)

    evaluator_script = os.path.join(
        os.path.dirname(__file__), "..", "evaluator", "quest_evaluator.py"
    )
    evaluator_script = os.path.abspath(evaluator_script)
    if not os.path.exists(evaluator_script):
        release_ports(quest_guid)
        raise HTTPException(status_code=500, detail=f"Evaluator script not found at {evaluator_script}")

    cmd = [
        sys.executable,
        evaluator_script,
        "--guid", quest_guid,
        "--type_id", str(request.type_id),
        "--sitl_port", str(sitl_port),
        "--proxy_port", str(proxy_port),
        "--manager_url", settings.public_base_url,
        "--internal_token", settings.internal_api_token,
        "--sim_vehicle_path", settings.sim_vehicle_path,
        "--vehicle", settings.sitl_vehicle,
        "--startup_delay", str(settings.sitl_startup_delay_sec),
        "--instance", str(proxy_port - settings.proxy_port_start),
    ] + list(settings.sitl_extra_args)

    try:
        proc = subprocess.Popen(cmd)
    except Exception as exc:
        release_ports(quest_guid)
        raise HTTPException(status_code=500, detail=f"Failed to start evaluator: {exc}")

    running_evaluators[quest_guid] = proc
    new_instance.status = models.QuestStatus.running
    db.commit()

    return {
        "success": True,
        "data": {
            "type_id": quest_type.id,
            "name": quest_type.name,
            "desc": quest_type.description,
            "quest_guid": quest_guid,
            "link": link,
        },
    }


@router.post("/stop/{quest_guid}", response_model=dict)
async def stop_quest(
    quest_guid: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    instance = db.query(models.QuestInstance).filter(models.QuestInstance.guid == quest_guid).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Quest instance not found")
    if instance.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your quest")

    stop_evaluator_process(quest_guid)
    release_ports(quest_guid)

    instance.status = models.QuestStatus.aborted
    instance.completed_at = datetime.now()
    db.commit()

    return {"success": True, "data": None}


@router.get("/log/{quest_guid}", response_model=dict)
async def get_quest_log(
    quest_guid: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    instance = db.query(models.QuestInstance).filter(models.QuestInstance.guid == quest_guid).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Quest instance not found")
    if instance.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your quest")

    log_path = os.path.join("logs", f"{quest_guid}.log")
    if not os.path.exists(log_path):
        return {"success": True, "data": {"quest_guid": quest_guid, "log": "Логи не найдены"}}

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"success": True, "data": {"quest_guid": quest_guid, "log": content}}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ошибка чтения лога: {exc}")


@router.get("/", response_model=dict)
async def get_quest_history(
    skip: int = Query(0, ge=0),
    take: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, pattern="^(pending|running|completed|aborted)$"),
    type_id: Optional[int] = Query(None),
    started: Optional[datetime] = Query(None),
    completed: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.QuestInstance).filter(models.QuestInstance.user_id == current_user.id)

    if status:
        query = query.filter(models.QuestInstance.status == models.QuestStatus(status))
    if type_id:
        query = query.filter(models.QuestInstance.type_id == type_id)
    if started:
        query = query.filter(models.QuestInstance.started_at >= started)
    if completed:
        query = query.filter(models.QuestInstance.completed_at <= completed)

    total = db.query(models.QuestInstance).filter(models.QuestInstance.user_id == current_user.id).count()
    filtered = query.count()
    instances = query.order_by(models.QuestInstance.started_at.desc()).offset(skip).limit(take).all()

    items = []
    for inst in instances:
        items.append({
            "type_id": inst.type_id,
            "quest_guid": inst.guid,
            "status": inst.status.value,
            "started": inst.started_at.isoformat() if inst.started_at else None,
            "completed": inst.completed_at.isoformat() if inst.completed_at else None,
            "max_time_sec": inst.max_time_sec,
            "elapsed_time_sec": inst.elapsed_time_sec,
            "result": inst.result.value if inst.result else None,
        })

    return {
        "success": True,
        "data": {
            "skip": skip,
            "take": take,
            "filtered": filtered,
            "total": total,
            "list": items,
        },
    }


@router.post("/{quest_guid}/progress")
async def update_quest_progress(
    quest_guid: str,
    progress: dict,
    db: Session = Depends(get_db),
    x_internal_token: str = Header(default=""),
):
    """Внутренний эндпоинт. Его вызывает только Quest Evaluator."""
    if x_internal_token != settings.internal_api_token:
        raise HTTPException(status_code=401, detail="Invalid internal token")

    instance = db.query(models.QuestInstance).filter(models.QuestInstance.guid == quest_guid).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Quest instance not found")

    instance.progress_data = progress

    if "elapsed_time_sec" in progress:
        instance.elapsed_time_sec = progress["elapsed_time_sec"]
    if "status" in progress:
        instance.status = models.QuestStatus(progress["status"])
    if "result" in progress:
        instance.result = models.QuestResult(progress["result"])
    if "completed_at" in progress and progress["completed_at"]:
        instance.completed_at = datetime.fromisoformat(progress["completed_at"])

    if progress.get("status") in {models.QuestStatus.completed.value, models.QuestStatus.aborted.value}:
        release_ports(quest_guid)
        running_evaluators.pop(quest_guid, None)

    db.commit()
    return {"success": True, "data": None}


@router.get("/{quest_guid}", response_model=dict)
async def get_quest_status(
    quest_guid: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    instance = db.query(models.QuestInstance).filter(models.QuestInstance.guid == quest_guid).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Quest instance not found")
    if instance.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your quest")

    quest_type = instance.quest_type
    checklist = []
    if quest_type.criteria:
        progress_map = {}
        if instance.progress_data and "checklist" in instance.progress_data:
            for item in instance.progress_data["checklist"]:
                progress_map[item["check_id"]] = item.get("progress", 0)
        for c in quest_type.criteria:
            checklist.append({
                "check_id": c["check_id"],
                "name": c["name"],
                "desc": c.get("desc", ""),
                "progress": progress_map.get(c["check_id"], 0),
            })

    return {
        "success": True,
        "data": {
            "type_id": instance.type_id,
            "quest_guid": instance.guid,
            "link": instance.link,
            "status": instance.status.value,
            "started": instance.started_at.isoformat() if instance.started_at else None,
            "completed": instance.completed_at.isoformat() if instance.completed_at else None,
            "result": instance.result.value if instance.result else None,
            "max_time_sec": instance.max_time_sec,
            "elapsed_time_sec": instance.elapsed_time_sec,
            "checklist": checklist,
        },
    }
