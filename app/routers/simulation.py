from fastapi import APIRouter
from app.worker.controller import (
    start_simulation_task,
    stop_simulation_task,
    restart_simulation_task,
    reset_simulation_state,
    simulation_status,
)

router = APIRouter(
    prefix="/simulation",
    tags=['Simulation']
)

@router.post("/start")
def start_sim():
    result = start_simulation_task()
    return result

@router.post("/stop")
def stop_sim():
    stopped = stop_simulation_task()
    return {"message": "Simulation stopped." if stopped else "Was not running."}

@router.post("/restart")
def restart_sim():
    restart = restart_simulation_task()
    return {"message": "Simulation restarted." if restart else "Restart failed."}


@router.get("/status")
def get_status():
    return {"status": simulation_status()}

@router.post("/reset")
def reset_simulation():
    reset_simulation_state()
    return {"message": "Simulation reset: all robots and tasks reset."}