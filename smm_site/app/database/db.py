# app/database/db.py
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- Настройки базы ---
DATABASE_URL = "sqlite:///./boostix.db"  # создаст файл boostix.db в корне проекта

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Модель пользователя ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    balance = Column(Float, default=0.0)  # баланс пользователя

# --- Создание таблиц ---
Base.metadata.create_all(bind=engine)

# --- Функции для работы с пользователями ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user(db, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db, username: str):
    user = User(username=username, balance=0.0)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_balance(db, username: str):
    user = get_user(db, username)
    return user.balance if user else 0.0

def update_balance(db, username: str, amount: float):
    user = get_user(db, username)
    if user:
        user.balance = amount
        db.commit()
        db.refresh(user)
        return user.balance
    return 0.0
