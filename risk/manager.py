import logging
from datetime import datetime, time

import numpy as np
import pandas as pd
from pydantic import BaseModel

# --- Data Models ---
class Order(BaseModel):
    symbol: str
    quantity: int
    price: float
    transaction_type: str  # "BUY" or "SELL"

class Portfolio(BaseModel):
    cash: float
    equity: float
    positions: dict[str, int]  # {symbol: quantity}
    historical_returns: pd.Series
    daily_equity: pd.Series

# --- RiskManager Class ---
class RiskManager:
    def __init__(self, max_daily_drawdown: float = 0.01, var_confidence_level: float = 0.95):
        self.max_daily_drawdown = max_daily_drawdown
        self.var_confidence_level = var_confidence_level
        self.daily_peak_equity = 0.0

    def _update_daily_peak_equity(self, current_equity: float):
        """Updates the peak equity for the current day."""
        now = datetime.now().time()
        # Reset peak at the start of a new trading day (e.g., 9:15 AM)
        if now < time(9, 16):
            self.daily_peak_equity = current_equity
        else:
            self.daily_peak_equity = max(self.daily_peak_equity, current_equity)

    def check_daily_drawdown(self, portfolio: Portfolio) -> bool:
        """Checks if the daily drawdown limit has been breached."""
        self._update_daily_peak_equity(portfolio.equity)
        drawdown = (self.daily_peak_equity - portfolio.equity) / self.daily_peak_equity

        if drawdown > self.max_daily_drawdown:
            logging.warning(f"Daily drawdown limit of {self.max_daily_drawdown:.2%} breached. Current drawdown: {drawdown:.2%}")
            return True
        return False

    def calculate_var_hist_sim(self, portfolio_returns: pd.Series) -> float:
        """Calculates Value at Risk (VaR) using historical simulation."""
        if portfolio_returns.empty:
            return 0.0

        losses = -portfolio_returns
        var = losses.quantile(self.var_confidence_level)
        return var

    def allow_order(self, order: Order, portfolio: Portfolio) -> bool:
        """
        Determines if an order should be allowed based on risk checks.
        """
        # 1. Check daily drawdown
        if self.check_daily_drawdown(portfolio):
            return False

        # 2. Pre-trade VaR check (simplified)
        # A more robust implementation would recalculate portfolio returns with the new position.
        # Here, we use a simpler check: ensure the order size isn't excessive relative to VaR.

        current_var = self.calculate_var_hist_sim(portfolio.historical_returns)

        # Define a VaR limit (e.g., VaR should not exceed 5% of total equity)
        var_limit = portfolio.equity * 0.05

        if current_var > var_limit:
            logging.warning(f"Portfolio VaR ({current_var:.2f}) exceeds limit of {var_limit:.2f}. Blocking new trades.")
            return False

        # Check if the new order's value significantly increases risk
        order_value = order.quantity * order.price
        if order_value > (var_limit - current_var):
             logging.warning(f"Order value ({order_value:.2f}) is too large relative to available VaR headroom. Blocking order.")
             return False

        logging.info("Order is within risk limits.")
        return True

# --- Example Usage ---
if __name__ == "__main__":
    # This is a simplified example. In a real system, the portfolio and order
    # would be managed by other components.

    # Sample historical returns for the portfolio
    np.random.seed(42)
    re_ts = pd.to_datetime(pd.date_range(start='2023-01-01', periods=1000, freq='D'))
    returns = pd.Series(np.random.normal(-0.001, 0.02, 1000), index=re_ts)

    # Sample daily equity curve
    eq_ts = pd.to_datetime(pd.date_range(start='2023-11-01', periods=100, freq='D'))
    equity_curve = pd.Series(100000 * (1 + np.random.normal(0, 0.01, 100)).cumprod(), index=eq_ts)

    # Initialize portfolio and risk manager
    portfolio_state = Portfolio(
        cash=50000,
        equity=105000,
        positions={"GOOGL": 10},
        historical_returns=returns,
        daily_equity=equity_curve
    )
    risk_manager = RiskManager()

    # Create a sample order
    new_order = Order(symbol="AAPL", quantity=5, price=150.0, transaction_type="BUY")

    # Check if the order is allowed
    is_allowed = risk_manager.allow_order(new_order, portfolio_state)
    logging.info(f"Is the order allowed? {is_allowed}")

    # Example of a drawdown breach
    portfolio_state.equity = 90000
    risk_manager.daily_peak_equity = 100000
    is_allowed_after_dd = risk_manager.allow_order(new_order, portfolio_state)
    logging.info(f"Is order allowed after drawdown? {is_allowed_after_dd}")
