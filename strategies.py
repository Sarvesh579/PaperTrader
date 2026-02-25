class BaseStrategy:
    def generate_signal(self, price, position):
        """
        Must return:
        {   "action": "BUY" / "SELL" / "HOLD",
            "quantity": float                    }
        """
        raise NotImplementedError

# -----------------------------------
# Example Strategy 1: Random Strategy
# -----------------------------------
import random

class RandomStrategy(BaseStrategy):
    def generate_signal(self, price, position):
        action = random.choice(["BUY", "SELL", "HOLD"])
        return {
            "action": action,
            "quantity": 10
        }

# -----------------------------------
# Example Strategy 2: Simple Momentum
# -----------------------------------
class MomentumStrategy(BaseStrategy):
    def __init__(self):
        self.last_price = {}  # symbol -> last price

    def generate_signal(self, price, position, symbol=None):

        if symbol not in self.last_price:
            self.last_price[symbol] = price
            return {"action": "HOLD", "quantity": 0}

        if price > self.last_price[symbol]:
            signal = {"action": "BUY", "quantity": 10}
        elif price < self.last_price[symbol]:
            signal = {"action": "SELL", "quantity": 10}
        else:
            signal = {"action": "HOLD", "quantity": 0}

        self.last_price[symbol] = price
        return signal

# -----------------------------------
# Strategy Registry
# -----------------------------------
AVAILABLE_STRATEGIES = {
    "random": RandomStrategy,
    "momentum": MomentumStrategy
}