from apscheduler.schedulers.background import BackgroundScheduler
from db import SessionLocal, SystemState
from datetime import datetime

scheduler = BackgroundScheduler()
scheduler.start()


def run_scheduled_tick(trader):
    trader.run_tick()

    # Update heartbeat
    db = SessionLocal()
    state = db.query(SystemState).first()
    if state:
        state.last_heartbeat = datetime.utcnow()
        db.commit()
    db.close()


def start_scheduler(trader):
    db = SessionLocal()
    state = db.query(SystemState).first()

    if state and not state.is_running:
        scheduler.add_job(
            run_scheduled_tick,
            "interval",
            minutes=state.interval_minutes,
            args=[trader],
            id="trading_job",
            replace_existing=True,
        )
        state.is_running = True
        db.commit()

    db.close()


def stop_scheduler():
    db = SessionLocal()
    state = db.query(SystemState).first()

    if scheduler.get_job("trading_job"):
        scheduler.remove_job("trading_job")

    if state:
        state.is_running = False
        db.commit()

    db.close()


def update_interval(minutes, trader):
    db = SessionLocal()
    state = db.query(SystemState).first()

    if state:
        state.interval_minutes = minutes
        db.commit()

    db.close()

    # Restart scheduler if running
    if scheduler.get_job("trading_job"):
        stop_scheduler()
        start_scheduler(trader)