from fastapi import FastAPI
from trader import PaperTrader

app = FastAPI()
trader = PaperTrader()


@app.get("/tick")
def tick():
    return {"message": trader.run_tick()}


@app.get("/status")
def status():
    return {
        "cash": trader.cash
    }