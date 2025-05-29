from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from app.database import Base

class Robot(Base):
    __tablename__ = "robots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    start_x = Column(Float, default=0.0)
    start_y = Column(Float, default=0.0)
    current_x = Column(Float, default=0.0)
    current_y = Column(Float, default=0.0)
    current_task_id = Column(Integer, ForeignKey("tasks.id", name="fk_robot_current_task", use_alter=True), nullable=True)
    battery_level = Column(Float, default=100.0)
    status = Column(String, default="idle")  # idle, moving, charging

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    robot_id = Column(Integer, ForeignKey("robots.id", name="fk_robot", use_alter=True), nullable=True)
    target_x = Column(Float)
    target_y = Column(Float)
    complete = Column(Boolean, default=False)
    task_type = Column(String, default="normal")  # or: "charge", "pickup", etc.
    priority = Column(Integer, default=1) # higher = more urgent
    created_at = Column(DateTime, default=datetime.utcnow)