from fastapi import FastAPI
from trader import PaperTrader

app = FastAPI()
trader = PaperTrader("random") # You can choose different strategies here


@app.get("/tick")
def tick():
    return {"message": trader.run_tick()}


@app.get("/status")
def status():
    return {
        "cash": trader.cash
    }


@app.post("/set_strategy/{strategy_name}")
def set_strategy(strategy_name: str):
    global trader
    trader = PaperTrader(strategy_name)
    return {"message": f"Strategy changed to {strategy_name}"}