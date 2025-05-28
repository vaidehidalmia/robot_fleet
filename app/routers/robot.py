from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models
from app import schemas

router = APIRouter(
    prefix="/robots",
    tags=['Robots']
)

@router.get("/", response_model=List[schemas.Robot])
def get_robots(db: Session = Depends(get_db)):
    robots = db.query(models.Robot).all()
    return robots

@router.get("/{id}", response_model=schemas.Robot)
def get_robot(id: int, db: Session = Depends(get_db)):
    robot = db.query(models.Robot).filter(models.Robot.id == id).first()
    if not robot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"robot with id: {id} not found")
    return robot

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Robot)
def create_robot(robot: schemas.RobotCreate, db: Session = Depends(get_db)):
    robot_data = robot.dict()
    
    # Set current_x/y to match start_x/y
    robot_data["current_x"] = robot_data["start_x"]
    robot_data["current_y"] = robot_data["start_y"]

    new_robot = models.Robot(**robot_data)
    db.add(new_robot)
    db.commit()
    db.refresh(new_robot)
    return new_robot

@router.delete("/{id}")
def delete_robot(id: int, db: Session = Depends(get_db)):
    robot_query = db.query(models.Robot).filter(models.Robot.id == id)
    robot = robot_query.first()
    if robot == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"robot with id: {id} does not exist")

    robot_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/{id}", response_model=schemas.Robot)
def update_robot(id: int, updated_robot: schemas.RobotCreate, db: Session = Depends(get_db)):
    robot_query = db.query(models.Robot).filter(models.Robot.id == id)
    robot = robot_query.first()
    if robot == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"robot with id: {id} does not exist")

    updated_robot_data = updated_robot.dict()
    updated_robot_data["current_x"] = updated_robot_data["start_x"]
    updated_robot_data["current_y"] = updated_robot_data["start_y"]
    robot_query.update(updated_robot_data, synchronize_session=False)
    db.commit()
    return robot_query.first()