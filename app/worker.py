import asyncio
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, movement

_simulation_task = None
_event_loop = None 
_simulation_status = "not started"  # "running", "finished", "stopped"

DRAIN_PER_UNIT = 1.0  # how much battery is drained per move
CHARGE_PER_TICK = 5.0  # how much battery is restored per second
LOW_BATTERY_THRESHOLD = 10.0


def init_worker(loop):
    global _event_loop
    _event_loop = loop

async def robot_movement_loop():
    global _simulation_status
    while True:
        db: Session = SessionLocal()
        try:
            tasks = db.query(models.Task).filter_by(complete=False).all()
            if not tasks:
                print("✅ All tasks complete. Stopping simulation.")
                _simulation_status = "finished"
                _simulation_task.cancel()
                return
            for task in tasks:
                robot = db.query(models.Robot).filter_by(id=task.robot_id).first()
                if not robot:
                    continue

                if robot.status == "charging":
                    robot.battery_level += CHARGE_PER_TICK
                    if robot.battery_level >= 100.0:
                        robot.battery_level = 100.0
                        robot.status = "idle"
                        print(f"Robot {robot.name} fully charged.")
                    db.commit()
                    continue

                if robot.battery_level < LOW_BATTERY_THRESHOLD:
                    robot.status = "charging"
                    print(f"Robot {robot.name} battery low. Switching to charging.")
                    db.commit()
                    continue

                distance, new_x, new_y, arrived = movement.move_toward(
                    robot.current_x, robot.current_y, task.target_x, task.target_y
                )

                robot.current_x = new_x
                robot.current_y = new_y
                robot.status = "moving"
                robot.battery_level -= distance * DRAIN_PER_UNIT

                if robot.battery_level < 0:
                    robot.battery_level = 0.0
                
                if arrived:
                    task.complete = True
                    robot.status = "idle"

                print(f"🔵 Robot {robot.name}: moved to ({new_x:.2f}, {new_y:.2f}), battery: {robot.battery_level:.1f}")

                db.commit()
        finally:
            db.close()

        await asyncio.sleep(1)

def start_simulation_task():
    global _simulation_task, _simulation_status
    if _simulation_task is None or _simulation_task.done():
        if _event_loop is None:
            raise RuntimeError("Event loop not initialized. Did you call init_worker()?")
        _simulation_task = asyncio.run_coroutine_threadsafe(robot_movement_loop(), _event_loop)
        _simulation_status = "running"
        print("Simulation started")
        return True
    print("Simulation already running...")
    return False

def stop_simulation_task():
    global _simulation_task, _simulation_status
    if _simulation_task and not _simulation_task.done():
        _simulation_task.cancel()
        _simulation_status = "stopped"
        print("Simulation stopped")
        return True
    print("Simulation was not running.")
    return False

def simulation_status():
    global _simulation_status
    return _simulation_status

def reset_simulation_state():
    global _simulation_status
    stop_simulation_task()

    db: Session = SessionLocal()
    try:
        # Reset robot positions
        robots = db.query(models.Robot).all()
        for robot in robots:
            robot.current_x = robot.start_x
            robot.current_y = robot.start_y
            robot.status = "idle"
            robot.battery_level = 100.0

        # Reset task completion
        tasks = db.query(models.Task).all()
        for task in tasks:
            task.complete = False

        db.commit()
        _simulation_status = "not started"
        print("Simulation reset: robot positions and tasks reset.")
    finally:
        db.close()