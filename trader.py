import yfinance as yf
import pandas as pd
from datetime import datetime
from db import SessionLocal, Trade, Position, EquityHistory, SystemState
from config import INITIAL_CAPITAL, BROKERAGE_RATE, DEFAULT_SYMBOL
from strategies import AVAILABLE_STRATEGIES

def get_or_create_system_state():
        db = SessionLocal()
        state = db.query(SystemState).first()

        if not state:
            state = SystemState(
                is_running=False,
                current_strategy="random",
                interval_minutes=5,
                initial_capital=INITIAL_CAPITAL,
                cash_balance=INITIAL_CAPITAL,
            )
            db.add(state)
            db.commit()
            db.refresh(state)

        db.close()
        return state

class PaperTrader:
    def __init__(self, strategy_name="random"):
        state = get_or_create_system_state()

        self.symbol = DEFAULT_SYMBOL
        self.strategy_name = strategy_name
        self.strategy = AVAILABLE_STRATEGIES[strategy_name]()
        self.cash = state.cash_balance


    # --------------------------
    # Fetch Latest Price
    # --------------------------
    def fetch_price(self):
        data = yf.download(self.symbol, period="1d", interval="1m", progress=False)

        if data.empty:
            return None

        # Proper MultiIndex check
        if isinstance(data.columns, pd.MultiIndex):
            price = data["Close"][self.symbol].iloc[-1]
        else:
            price = data["Close"].iloc[-1]

        return float(price)


    # --------------------------
    # Execute Order
    # --------------------------
    def execute_order(self, side, quantity, price):
        db = SessionLocal()

        trade_value = quantity * price
        brokerage = trade_value * BROKERAGE_RATE

        position = db.query(Position).filter(Position.symbol == self.symbol).first()
        state = db.query(SystemState).first()

        if side == "BUY":
            total_cost = trade_value + brokerage

            if self.cash < total_cost:
                db.close()
                return "Insufficient funds"

            self.cash -= total_cost

            if position:
                new_qty = position.quantity + quantity
                new_avg = ((position.avg_price * position.quantity) + trade_value) / new_qty
                position.quantity = new_qty
                position.avg_price = new_avg
            else:
                position = Position(
                    symbol=self.symbol,
                    quantity=quantity,
                    avg_price=price,
                    current_price=price,
                    unrealized_pnl=0,
                )
                db.add(position)

        elif side == "SELL":
            if not position or position.quantity < quantity:
                db.close()
                return "Not enough shares"

            self.cash += trade_value - brokerage
            realized_pnl = (price - position.avg_price) * quantity

            position.quantity -= quantity

            if position.quantity == 0:
                db.delete(position)

            db.add(
                Trade(
                    symbol=self.symbol,
                    side="SELL",
                    quantity=quantity,
                    price=price,
                    brokerage=brokerage,
                    total_value=trade_value,
                    realized_pnl=realized_pnl,
                )
            )

        # ✅ ALWAYS update DB cash
        state.cash_balance = self.cash

        db.commit()
        db.close()
        return "Order Executed"


    # --------------------------
    # Update Equity Snapshot
    # --------------------------
    def update_equity(self):
        db = SessionLocal()

        portfolio_value = 0
        positions = db.query(Position).all()

        for pos in positions:
            portfolio_value += pos.quantity * pos.current_price

        total_equity = self.cash + portfolio_value

        db.add(
            EquityHistory(
                cash_balance=self.cash,
                portfolio_value=portfolio_value,
                total_equity=total_equity,
            )
        )

        db.commit()
        db.close()

    # --------------------------
    # Manual Tick
    # --------------------------
    def run_tick(self):
        price = self.fetch_price()
        if not price:
            return "Price fetch failed"

        db = SessionLocal()
        position = db.query(Position).filter(Position.symbol == self.symbol).first()
        db.close()

        signal = self.strategy.generate_signal(price, position)

        action = signal["action"]
        quantity = signal["quantity"]

        if action in ["BUY", "SELL"] and quantity > 0:
            result = self.execute_order(action, quantity, price)
        else:
            result = "No Trade"

        self.update_equity()
        return result