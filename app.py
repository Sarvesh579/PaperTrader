from fastapi import FastAPI
from trader import PaperTrader
from scheduler import scheduler, start_scheduler, stop_scheduler, update_interval
from db import SessionLocal, SystemState, Position, Trade, EquityHistory
from config import INITIAL_CAPITAL


app = FastAPI()
trader = PaperTrader("random") # You can choose different strategies here

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
        "last_heartbeat": str(state.last_heartbeat) if state else None
    }
    return response


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
            "timestamp": str(t.timestamp),
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
    history = db.query(EquityHistory).order_by(EquityHistory.timestamp.asc()).all()

    data = [
        {
            "timestamp": str(h.timestamp),
            "total_equity": h.total_equity
        }
        for h in history
    ]

    db.close()
    return data


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

    # Stop scheduler if running
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
