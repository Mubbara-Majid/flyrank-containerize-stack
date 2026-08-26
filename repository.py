import os
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.getenv("DATABASE_URL", "postgres://postgres:dev@localhost:5432/tasks")

def get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT FALSE
            )
            """
        )
        cur.execute("SELECT COUNT(*) AS count FROM tasks")
        count = cur.fetchone()["count"]
        if count == 0:
            cur.executemany(
                "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                [
                    ("Buy milk", False),
                    ("Walk the dog", True),
                    ("Finish FlyRank assignment", False),
                ],
            )
    conn.commit()
    conn.close()

def list_tasks():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM tasks ORDER BY id")
        rows = cur.fetchall()
    conn.close()
    return rows
 
 
def get_task(task_id: int):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
        row = cur.fetchone()
    conn.close()
    return row


def create_task(title: str):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *",
            (title, False),
        )
        row = cur.fetchone()
    conn.commit()
    conn.close()
    return row


def update_task(task_id: int, title: str, done: bool):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *",
            (title, done, task_id),
        )
        row = cur.fetchone()
    conn.commit()
    conn.close()
    return row
 
 
def delete_task(task_id: int) -> bool:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,))
        row = cur.fetchone()
    conn.commit()
    conn.close()
    return row is not None