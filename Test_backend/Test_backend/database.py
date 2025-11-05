import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pymysql.constants import CLIENT

load_dotenv()

DB_USER = os.getenv("dbuser")
DB_PASSWORD = os.getenv("dbpassword")
DB_HOST = os.getenv("dbhost", "localhost")
DB_PORT = os.getenv("dbport", 3306)
DB_NAME = os.getenv("dbname")

db_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    db_url, connect_args={"client_flag": CLIENT.MULTI_STATEMENTS}, echo=True
)

SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

create_table_query = text(
    """
CREATE TABLE IF NOT EXISTS user_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL
);
"""
)

try:
    db.execute(create_table_query)
    db.commit()
    print("Table has been created successfully!")
except Exception as e:
    db.rollback()
    print(f"Error creating table: {e}")

db.close()
