# backend/app.py
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
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup (SQLite for simplicity)
DB_URL = "sqlite:///./test.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
db = engine.connect()

# Create tables if not exist
db.execute(
    text(
        """
CREATE TABLE IF NOT EXISTS user_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
"""
    )
)
db.execute(
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


# Pydantic models
class User(BaseModel):
    email: str
    password: str


class Expense(BaseModel):
    id: int = None
    title: str
    amount: float


# Helper: get current user from Authorization header
def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = db.execute(
            text("SELECT * FROM user_info WHERE id=:id"), {"id": payload["user_id"]}
        ).fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# Signup endpoint
@app.post("/signup")
def signup(user: User):
    existing = db.execute(
        text("SELECT * FROM user_info WHERE email=:email"), {"email": user.email}
    ).fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    hashed = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
    db.execute(
        text("INSERT INTO user_info (email, password) VALUES (:email, :password)"),
        {"email": user.email, "password": hashed.decode()},
    )
    db.commit()
    return {"message": "User created successfully"}


# Login endpoint
@app.post("/login")
def login(user: User):
    result = db.execute(
        text("SELECT * FROM user_info WHERE email=:email"), {"email": user.email}
    ).fetchone()
    if not result or not bcrypt.checkpw(
        user.password.encode(), result.password.encode()
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = jwt.encode({"user_id": result.id}, SECRET_KEY, algorithm="HS256")
    return {"token": token}


# Get all expenses
@app.get("/expenses")
def get_expenses(user=Depends(get_current_user)):
    rows = db.execute(
        text("SELECT * FROM expenses WHERE user_id=:uid"), {"uid": user.id}
    ).fetchall()
    return [dict(row) for row in rows]


# Create new expense
@app.post("/expenses")
def create_expense(expense: Expense, user=Depends(get_current_user)):
    db.execute(
        text(
            "INSERT INTO expenses (title, amount, user_id) VALUES (:title, :amount, :uid)"
        ),
        {"title": expense.title, "amount": expense.amount, "uid": user.id},
    )
    db.commit()
    return {"message": "Expense added"}


# Update expense
@app.put("/expenses/{expense_id}")
def update_expense(expense_id: int, expense: Expense, user=Depends(get_current_user)):
    result = db.execute(
        text(
            "UPDATE expenses SET title=:title, amount=:amount WHERE id=:id AND user_id=:uid"
        ),
        {
            "title": expense.title,
            "amount": expense.amount,
            "id": expense_id,
            "uid": user.id,
        },
    )
    db.commit()
    return {"message": "Expense updated"}


# Delete expense
@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int, user=Depends(get_current_user)):
    db.execute(
        text("DELETE FROM expenses WHERE id=:id AND user_id=:uid"),
        {"id": expense_id, "uid": user.id},
    )
    db.commit()
    return {"message": "Expense deleted"}


# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
