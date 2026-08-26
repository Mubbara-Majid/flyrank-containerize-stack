from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Path
from fastapi.responses import JSONResponse
import repository

repository.init_db()

app = FastAPI()

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