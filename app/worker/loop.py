import asyncio
import traceback
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal
from app import models
from app.worker.movement import move_toward
from app.worker.config import DRAIN_PER_UNIT, CHARGE_PER_TICK, LOW_BATTERY_THRESHOLD
from app.worker.simulation_context import SimulationContext

async def robot_movement_loop(context: SimulationContext):
    context.update_simulation_status("running")
    print("Simulation loop started.")

    try:
        while True:
            db: Session = SessionLocal()
            try:
                robots = db.query(models.Robot).all()

                for robot in robots:
                    # Low battery — ensure charge task exists
                    if robot.battery_level < LOW_BATTERY_THRESHOLD:
                        existing_charge_task = (
                            db.query(models.Task)
                            .filter_by(robot_id=robot.id, complete=False, task_type="charge")
                            .first()
                        )
                        if not existing_charge_task:
                            charging_task = models.Task(
                                robot_id=robot.id,
                                target_x=robot.start_x,
                                target_y=robot.start_y,
                                complete=False,
                                priority=999,
                                task_type="charge"
                            )
                            db.add(charging_task)
                            db.commit()
                            print(f"{robot.name} low battery. Added charging task.")
                            continue  # Skip movement this tick, will pick up charge task next

                    # Fetch highest priority pending task
                    task = (
                        db.query(models.Task)
                        .filter_by(robot_id=robot.id, complete=False)
                        .order_by(models.Task.priority.desc(), models.Task.created_at)
                        .first()
                    )

                    if not task:
                        robot.status = "idle"
                        continue

                    # Move toward task target
                    distance, new_x, new_y, arrived = move_toward(
                        robot.current_x, robot.current_y,
                        task.target_x, task.target_y
                    )

                    robot.current_x = new_x
                    robot.current_y = new_y
                    robot.battery_level -= distance * DRAIN_PER_UNIT
                    if robot.battery_level < 0:
                        robot.battery_level = 0.0

                    robot.status = "charging" if task.task_type == "charge" else "moving"
                    print(f"{robot.name}: moved to ({new_x:.2f}, {new_y:.2f}), battery: {robot.battery_level:.1f}")

                    # Task Completion
                    if task.task_type == "charge" and arrived:
                        robot.battery_level += CHARGE_PER_TICK
                        if robot.battery_level >= 100.0:
                            robot.battery_level = 100.0
                            task.complete = True
                            robot.status = "idle"
                            print(f"{robot.name} fully charged (task {task.id}).")

                    elif task.task_type == "normal" and arrived:
                        task.complete = True
                        robot.status = "idle"
                        print(f"{robot.name} completed task {task.id}.")

                    db.commit()

                # Stop simulation if all tasks are complete
                unfinished_tasks = db.query(models.Task).filter_by(complete=False).count()
                if unfinished_tasks == 0:
                    print("All tasks complete. Stopping simulation.")
                    context.update_simulation_status("finished")
                    context.cancel_simulation_task()
                    return

            except SQLAlchemyError as db_err:
                print("Database error in simulation loop:", db_err)
                traceback.print_exc()
                context.update_simulation_status("error")
                return

            except Exception as e:
                print("Unexpected error in simulation loop:", e)
                traceback.print_exc()
                context.update_simulation_status("error")
                return

            finally:
                db.close()

            await asyncio.sleep(1)

    except asyncio.CancelledError:
        print("Simulation loop cancelled.")
        context.update_simulation_status("stopped")

    except Exception as e:
        print("Fatal error in simulation loop:", e)
        traceback.print_exc()
        context.update_simulation_status("error")