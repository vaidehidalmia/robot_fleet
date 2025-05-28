import asyncio
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.worker.loop import robot_movement_loop
from app.worker.simulation_context import SimulationContext

_simulation_task = None
_event_loop = None
_simulation_status = "not started"  # can be: running, stopped, finished, error

# -- EVENT LOOP SETUP --
def init_worker(loop):
    global _event_loop
    _event_loop = loop

# -- STATUS TRACKING --
def update_simulation_status(status: str):
    global _simulation_status
    _simulation_status = status

def simulation_status():
    return _simulation_status


# -- SIMULATION MANAGEMENT --
def cancel_simulation_task():
    global _simulation_task
    if _simulation_task:
        _simulation_task.cancel()
        _simulation_task = None
        return True
    return False

def start_simulation_task():
    global _simulation_task

    if simulation_status() in {"finished", "error"}:
        print("Simulation finished. Cannot restart without reset.")
        return {"started": False, "message": "Cannot start: simulation already finished or errored. Please reset."}

    if _simulation_task is None or _simulation_task.done():
        if _event_loop is None:
            raise RuntimeError("Event loop not initialized. Did you call init_worker()?")

        context = SimulationContext(
            cancel_simulation_task=cancel_simulation_task,
            update_simulation_status=update_simulation_status,
        )

        _simulation_task = asyncio.run_coroutine_threadsafe(
            robot_movement_loop(context),
            _event_loop
        )
        print("Simulation task submitted.")
        return {"started": True, "message": "Simulation started."}

    print("Simulation already running...")
    return {"started": False, "message": "Simulation already running."}

def stop_simulation_task():
    if cancel_simulation_task():
        update_simulation_status("stopped")
        print("Simulation stopped.")
        return True
    print("Simulation was not running.")
    return False

def restart_simulation_task():
    stopped = stop_simulation_task()
    started = start_simulation_task()
    return stopped and started

def reset_simulation_state():
    stop_simulation_task()

    db: Session = SessionLocal()
    try:
        # Reset robots
        robots = db.query(models.Robot).all()
        for robot in robots:
            robot.current_x = robot.start_x
            robot.current_y = robot.start_y
            robot.status = "idle"
            robot.battery_level = 100.0

        # Delete all "charge" tasks
        db.query(models.Task).filter_by(task_type="charge").delete()

        # Reset all other task completions
        db.query(models.Task).filter(models.Task.task_type != "charge").update(
            {models.Task.complete: False}, synchronize_session=False
        )

        db.commit()
        update_simulation_status("not started")
        print("Simulation reset: robot positions and tasks reset.")
    finally:
        db.close()