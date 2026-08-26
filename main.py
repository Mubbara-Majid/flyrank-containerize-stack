from dotenv import load_dotenv
load_dotenv()
import repository
repository.init_db()

from fastapi import FastAPI, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

class TaskCreate(BaseModel):
    title: str = ""


@app.get("/", description="Endpoint describing the API.")
def hello():
    return {"name": "Task API", "version": "1.0", "endpoints": "/, /health"}


@app.get("/health", description="Give the status of the API.")
def health():
    return {"status": "OK"}


@app.get("/tasks", description="List all the tasks.")
def tasks():
    return repository.list_tasks()


@app.get("/tasks/{id}", description="Returns task according to the ID.")
def task_id(id: int= Path(..., description="ID of the task.", example=1)):

    task = repository.get_task(id)

    if task is None:
        return JSONResponse(status_code=404, content={"error": f"Task of ID {id} not found!"})
    return task

@app.post("/tasks", description="Create a new task.")
def add_task(task: TaskCreate):

    if not task.title.strip():
        return JSONResponse(status_code=400, content={"error": "Title is required"})

    row = repository.create_task(task.title)

    return JSONResponse(status_code=201, content=row)
    