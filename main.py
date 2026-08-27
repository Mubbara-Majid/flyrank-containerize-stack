from dotenv import load_dotenv
load_dotenv()

import repository
repository.init_db()

from supabase_client import supabase
from auth import sign_up as auth_sign_up, sign_in as auth_sign_in

from fastapi import FastAPI, Path
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from typing import Optional

app = FastAPI()

#---------------------------Pydantic Classes
class TaskCreate(BaseModel):
    title: str = ""


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


class LoginIn(BaseModel):
    email: str = ""
    password: str = ""


class SignUp(BaseModel):
    email: str = ""
    password: str = ""

# ------------------------ROUTES

# ------------------------Landing Page
@app.get("/", description="Endpoint describing the API.")
def hello():
    return {"name": "Task API", "version": "1.0", "endpoints": "/, /health"}

#--------------------------Health Check
@app.get("/health", description="Give the status of the API.")
def health():
    return {"status": "OK"}

# ---------------------------Sign Up
@app.post("/auth/signup", description="Sign Up with Email and Password")
def sign_up(credentials: SignUp):
    if not credentials.email.strip() or not credentials.password.strip():
        return JSONResponse(status_code=400, content={"error": "Email and password required"})
    
    try:
        result = auth_sign_up(credentials.email, credentials.password)

        return JSONResponse(status_code=201, content={"user": str(result.user)})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


# ---------------------------Log In
@app.post("/auth/login", description="Login with Email and Password")
def login(credentials: LoginIn):
    if not credentials.email.strip() or not credentials.password.strip():
        return JSONResponse(status_code=400, content={"error": "Email and password required"})
    
    try:
        result = auth_sign_in(credentials.email, credentials.password)
        return {
            "refresh_token": result.session.refresh_token,
            "access_token": result.session.access_token, 
            "token_type": "bearer"
        }
    except Exception as e:
        return JSONResponse(status_code=401, content={"error": "Invalid email or password"})
 

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


@app.put("/tasks/{id}", description="Update a Task.")
def updated_task(id: int, updated_task: TaskUpdate):

    row = repository.get_task(id)

    if row is None:
        return JSONResponse(status_code=404, content={"error": f"Task ID {id} not found!"})

    updated_info = updated_task.model_dump(exclude_unset=True)

    if not updated_info:
        return JSONResponse(status_code=400, content={"error": f"No fields provided for task ID {id}"})
    
    if "title" in updated_info and not updated_info["title"].strip():
        return JSONResponse(status_code=400, content={"error": "title cannot be empty"})
 
    new_title = updated_info.get("title", row["title"])
    new_done = updated_info.get("done", row["done"])
 
    updated_row = repository.update_task(id, new_title, new_done)
    return JSONResponse(status_code=200, content=updated_row)


@app.delete("/tasks/{id}", description="Delete task by ID.")
def delete_task(id: int = Path(..., description="Task ID", example=1)):

    row = repository.get_task(id)

    if row is None:
        return JSONResponse(status_code=404, content={"error": f"Task ID {id} not found!"})

    repository.delete_task(id)

    return Response(status_code=204)