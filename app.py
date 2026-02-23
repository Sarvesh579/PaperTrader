from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from trader import PaperTrader
from scheduler import scheduler, start_scheduler, stop_scheduler, update_interval
from db import SessionLocal, SystemState, Position, Trade, EquityHistory
from config import INITIAL_CAPITAL
from datetime import datetime, timedelta
from sqlalchemy import and_
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
def to_ist(dt):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(IST)
    return dt.astimezone(IST)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
db = SessionLocal()
state = db.query(SystemState).first()
db.close()

initial_strategy = state.current_strategy if state else "random"
trader = PaperTrader(initial_strategy)

@app.on_event("startup")
def resume_if_running():
    db = SessionLocal()
    state = db.query(SystemState).first()
    db.close()

    if state and state.is_running:
        start_scheduler(trader)


@app.get("/tick")
def tick():
    return {"message": trader.run_tick()}


@app.get("/status")
def status():
    db = SessionLocal()
    state = db.query(SystemState).first()
    db.close()
    response = {
        "cash": state.cash_balance if state else None,
        "is_running": state.is_running if state else False,
        "interval_minutes": state.interval_minutes if state else None,
        "current_strategy": state.current_strategy if state else None,
        "last_heartbeat": to_ist(state.last_heartbeat).isoformat()
    }
    return response


@app.get("/strategy")
def get_strategy():
    db = SessionLocal()
    state = db.query(SystemState).first()
    db.close()
    return {
        "current_strategy": state.current_strategy if state else None
    }


@app.get("/portfolio")
def portfolio():
    db = SessionLocal()
    positions = db.query(Position).all()
    data = [
        {
            "symbol": p.symbol,
            "quantity": p.quantity,
            "avg_price": p.avg_price,
            "current_price": p.current_price,
            "unrealized_pnl": p.unrealized_pnl,
        }
        for p in positions
    ]
    db.close()
    return data


@app.get("/trades")
def trades():
    db = SessionLocal()
    trades = db.query(Trade).order_by(Trade.timestamp.desc()).all()
    data = [
        {
            "timestamp": to_ist(t.timestamp).isoformat(),
            "symbol": t.symbol,
            "side": t.side,
            "quantity": t.quantity,
            "price": t.price,
            "realized_pnl": t.realized_pnl,
        }
        for t in trades
    ]
    db.close()
    return data


@app.get("/equity")
def equity():
    db = SessionLocal()
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    last_24h = now - timedelta(hours=24)

    history = (
        db.query(EquityHistory)
        .filter(EquityHistory.timestamp >= last_24h)
        .order_by(EquityHistory.timestamp.asc())
        .all()
    )
    db.close()

    if len(history) <= 20:
        return [{
            "timestamp" : to_ist(h.timestamp).isoformat(),
            "total_equity": h.total_equity
            }
        for h in history
        ]
    condensed = []
    bucket = None
    current_bucket_time = None
    for h in history:
        bucket_time = h.timestamp.replace(
            minute=(h.timestamp.minute // 15) * 15,
            second=0,
            microsecond=0
        )
        if current_bucket_time != bucket_time:
            condensed.append({
                "timestamp": to_ist(bucket_time).isoformat(),
                "total_equity": h.total_equity
            })
            current_bucket_time = bucket_time
    return condensed


@app.get("/refresh_prices")
def refresh_prices():
    db = SessionLocal()
    positions = db.query(Position).all()

    for pos in positions:
        price = trader.fetch_price()
        pos.current_price = price
        pos.unrealized_pnl = (price - pos.avg_price) * pos.quantity

    db.commit()
    db.close()
    return {"message": "Prices refreshed"}


@app.post("/start")
def start():
    start_scheduler(trader)
    return {"message": "Trading started"}


@app.post("/reset")
def reset():
    # Stop scheduler first
    stop_scheduler()

    db = SessionLocal()

    state = db.query(SystemState).first()
    state.cash_balance = INITIAL_CAPITAL
    state.is_running = False

    # Clear positions
    db.query(Position).delete()

    # Clear trades
    db.query(Trade).delete()

    # Clear equity history
    db.query(EquityHistory).delete()

    db.commit()
    db.close()

    return {"message": "Account reset successful"}


@app.post("/set_cash/{amount}")
def set_cash(amount: float):
    db = SessionLocal()
    state = db.query(SystemState).first()

    state.cash_balance = amount

    db.commit()
    db.close()

    return {"message": f"Cash updated to {amount}"}


@app.post("/set_strategy/{strategy_name}")
def set_strategy(strategy_name: str):
    global trader

    stop_scheduler()

    db = SessionLocal()
    state = db.query(SystemState).first()
    state.current_strategy = strategy_name
    db.commit()
    db.close()

    trader = PaperTrader(strategy_name)

    return {"message": f"Strategy changed to {strategy_name}"}


@app.post("/set_interval/{minutes}")
def set_interval(minutes: int):
    update_interval(minutes, trader)
    return {"message": f"Interval set to {minutes} minutes"}


@app.post("/stop")
def stop():
    stop_scheduler()
    return {"message": "Trading stopped"}
