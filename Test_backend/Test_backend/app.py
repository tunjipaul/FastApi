from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import bcrypt
import jwt
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "secret")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URL = "sqlite:///./test.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})

with engine.begin() as conn:
    conn.execute(
        text(
            """
CREATE TABLE IF NOT EXISTS user_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
"""
        )
    )

    conn.execute(
        text(
            """
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    amount REAL NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user_info(id)
)
"""
        )
    )


class User(BaseModel):
    username: str
    email: str
    password: str

class LoginUser(BaseModel):
    email: str
    password: str

class Expense(BaseModel):
    id: int = None
    title: str
    amount: float


def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = parts[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        with engine.connect() as conn:
            row = (
                conn.execute(
                    text("SELECT * FROM user_info WHERE id=:id"), {"id": user_id}
                )
                .mappings()
                .fetchone()
            )

        if not row:
            raise HTTPException(status_code=401, detail="Invalid token user")

        return row

    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/signup")
def signup(user: User):
    with engine.connect() as conn:
        existing = conn.execute(
            text("SELECT * FROM user_info WHERE email=:email"), {"email": user.email}
        ).fetchone()

    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())

    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO user_info (username, email, password) VALUES (:username, :email, :password)"
            ),
            {
                "username": user.username,
                "email": user.email,
                "password": hashed.decode(),
            },
        )

    return {"message": "User created successfully"}


@app.post("/login")
def login(user: LoginUser):
    with engine.connect() as conn:
        result = (
            conn.execute(
                text("SELECT * FROM user_info WHERE email=:email"),
                {"email": user.email},
            )
            .mappings()
            .fetchone()
        )

    if not result or not bcrypt.checkpw(
        user.password.encode(), result["password"].encode()
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = jwt.encode({"user_id": result["id"]}, SECRET_KEY, algorithm="HS256")
    return {"token": token}


@app.get("/expenses")
def get_expenses(user=Depends(get_current_user)):
    with engine.connect() as conn:
        rows = (
            conn.execute(
                text("SELECT * FROM expenses WHERE user_id=:uid"),
                {"uid": user["id"]},
            )
            .mappings()
            .fetchall()
        )
    return rows


@app.post("/expenses")
def create_expense(expense: Expense, user=Depends(get_current_user)):
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO expenses (title, amount, user_id) VALUES (:title, :amount, :uid)"
            ),
            {"title": expense.title, "amount": expense.amount, "uid": user["id"]},
        )
    return {"message": "Expense added"}


@app.put("/expenses/{expense_id}")
def update_expense(expense_id: int, expense: Expense, user=Depends(get_current_user)):
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE expenses SET title=:title, amount=:amount WHERE id=:id AND user_id=:uid"
            ),
            {
                "title": expense.title,
                "amount": expense.amount,
                "id": expense_id,
                "uid": user["id"],
            },
        )
    return {"message": "Expense updated"}


@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, user=Depends(get_current_user)):
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM expenses WHERE id=:id AND user_id=:uid"),
            {"id": expense_id, "uid": user["id"]},
        )
    return {"message": "Expense deleted"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8000)
