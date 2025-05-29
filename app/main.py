from fastapi import FastAPI
import asyncio

# frontend
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

from app.database import Base, engine, get_db
from app.routers import robot, task, simulation
from app import models
from app import schemas
from app.worker.controller import init_worker, stop_simulation_task

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")


app.include_router(robot.router)
app.include_router(task.router)
app.include_router(simulation.router)

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_running_loop()
    init_worker(loop)

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down simulation...")
    stop_simulation_task() 

@app.get("/viz", response_class=HTMLResponse)
def read_index():
    with open("app/static/index.html") as f:
        return f.read()

@app.get("/")
def main():
    return {"message": "Robot Fleet API running..."}