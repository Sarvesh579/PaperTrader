from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///database.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


# -------------------------
# Trades Table
# -------------------------
class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    symbol = Column(String)
    side = Column(String)  # BUY / SELL
    quantity = Column(Float)
    price = Column(Float)
    brokerage = Column(Float)
    total_value = Column(Float)
    realized_pnl = Column(Float)


# -------------------------
# Positions Table
# -------------------------
class Position(Base):
    __tablename__ = "positions"

    symbol = Column(String, primary_key=True, index=True)
    quantity = Column(Float)
    avg_price = Column(Float)
    current_price = Column(Float)
    unrealized_pnl = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)


# -------------------------
# Equity History Table
# -------------------------
class EquityHistory(Base):
    __tablename__ = "equity_history"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    cash_balance = Column(Float)
    portfolio_value = Column(Float)
    total_equity = Column(Float)


# -------------------------
# System State Table
# -------------------------
class SystemState(Base):
    __tablename__ = "system_state"

    id = Column(Integer, primary_key=True, index=True)
    is_running = Column(Boolean, default=False)
    current_strategy = Column(String)
    interval_minutes = Column(Integer)
    initial_capital = Column(Float)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)


# Create all tables
Base.metadata.create_all(bind=engine)