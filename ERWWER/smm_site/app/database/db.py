# app/database/db.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./boostix.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    balance = Column(Float, default=0.0)


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    provider = Column(String)            # "crystalpay" | "cryptobot"
    external_id = Column(String, index=True, nullable=True)  # invoice id at provider
    amount_rub = Column(Float, default=0.0)
    amount_usdt = Column(Float, default=0.0)
    status = Column(String, default="pending")  # pending | paid | failed
    pay_url = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


Base.metadata.create_all(bind=engine)


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


def add_balance(db, username: str, delta: float):
    user = get_user(db, username) or create_user(db, username)
    user.balance = (user.balance or 0.0) + delta
    db.commit()
    db.refresh(user)
    return user.balance


def create_invoice_record(db, username: str, provider: str, amount_rub: float,
                          amount_usdt: float, external_id: str | None,
                          pay_url: str | None) -> Invoice:
    inv = Invoice(
        username=username,
        provider=provider,
        external_id=external_id,
        amount_rub=amount_rub,
        amount_usdt=amount_usdt,
        status="pending",
        pay_url=pay_url,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def get_invoice(db, invoice_id: int) -> Invoice | None:
    return db.query(Invoice).filter(Invoice.id == invoice_id).first()


def get_invoice_by_external(db, provider: str, external_id: str) -> Invoice | None:
    return db.query(Invoice).filter(
        Invoice.provider == provider,
        Invoice.external_id == str(external_id)
    ).first()


def mark_invoice_paid(db, invoice_id: int) -> Invoice | None:
    inv = get_invoice(db, invoice_id)
    if inv and inv.status != "paid":
        inv.status = "paid"
        db.commit()
        db.refresh(inv)
    return inv
