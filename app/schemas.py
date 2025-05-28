from pydantic import BaseModel

# --- Robot schemas ---
class RobotBase(BaseModel):
    name: str 
    start_x: float = 0.0
    start_y: float = 0.0
    status: str = "idle" # idle, moving, charging
    battery_level: float = 100.0

class RobotCreate(RobotBase):
    pass


class Robot(RobotBase):
    id: int
    current_x: float
    current_y: float
    battery_level: float
    class Config:
        from_attributes = True

# --- Task schemas ---
class TaskBase(BaseModel):
    robot_id: int
    target_x: float
    target_y: float

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
        complete: bool

class Task(TaskBase):
    id: int
    complete: bool
    class Config:
        from_attributes = True