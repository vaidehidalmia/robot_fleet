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
    print("✅ Simulation loop started.")

    try:
        while True:
            db: Session = SessionLocal()
            try:
                tasks = db.query(models.Task).filter_by(complete=False).all()
                if not tasks:
                    print("✅ All tasks complete. Stopping simulation.")
                    context.update_simulation_status("finished")
                    context.cancel_simulation_task()
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

                    distance_travelled, new_x, new_y, arrived = move_toward(
                        robot.current_x, robot.current_y,
                        task.target_x, task.target_y
                    )

                    robot.current_x = new_x
                    robot.current_y = new_y
                    robot.status = "moving"
                    robot.battery_level -= distance_travelled * DRAIN_PER_UNIT

                    if robot.battery_level < 0:
                        robot.battery_level = 0.0

                    if arrived:
                        task.complete = True
                        robot.status = "idle"
                        db.commit()
                        continue

                    print(f"🔵 Robot {robot.name}: moved to ({new_x:.2f}, {new_y:.2f}), battery: {robot.battery_level:.1f}")
                    db.commit()

            except SQLAlchemyError as db_err:
                print("❌ Database error:", db_err)
                traceback.print_exc()
                context.update_simulation_status("error")
                return

            except Exception as e:
                print("❌ Unexpected error in loop:", e)
                traceback.print_exc()
                context.update_simulation_status("error")
                return

            finally:
                db.close()

            await asyncio.sleep(1)

    except asyncio.CancelledError:
        print("🛑 Simulation loop cancelled.")
        context.update_simulation_status("stopped")

    except Exception as e:
        print("🔥 Fatal error in simulation loop:", e)
        traceback.print_exc()
        context.update_simulation_status("error")