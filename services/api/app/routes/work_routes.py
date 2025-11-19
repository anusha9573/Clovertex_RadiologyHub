from datetime import date, time as time_type
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.api.app.controllers.assignment_controller import AssignmentController
from services.api.app.db.repositories import WorkRequestsRepo

router = APIRouter(tags=["work-management"])
controller = AssignmentController()


class AddWorkRequest(BaseModel):
    work_type: str
    description: str
    priority: int
    scheduled_date: date
    scheduled_time: time_type


@router.post("/add_work")
def add_work(req: AddWorkRequest):
    result = controller.add_work(req.dict())
    return {"status": "ok", "result": result}


@router.post("/assign/{work_id}")
def assign_work(
    work_id: str,
    use_background_llm: bool = Query(
        default=True,
        description="If true, use lightweight template provider; false attempts HF provider.",
    ),
):
    try:
        llm_provider = "template" if use_background_llm else "hf"
        assignment = controller.assign(work_id, llm_provider=llm_provider)
        return {"status": "ok", "assignment": assignment}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/status/{work_id}")
def status(work_id: str):
    work = controller.fetch_status(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="work not found")
    return {"status": "ok", "work": work}


@router.get("/work")
def list_work(limit: int = 25, status: Optional[str] = None):
    rows = WorkRequestsRepo.list_work_requests(limit=limit, status=status)
    return {"status": "ok", "work_requests": rows}


@router.get("/pipeline/{work_id}")
def pipeline_details(work_id: str, use_background_llm: bool = True):
    try:
        llm_provider = "template" if use_background_llm else "hf"
        data = controller.run_pipeline_verbose(work_id, llm_provider=llm_provider)
        return {"status": "ok", "pipeline": data}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
