import logging
import os
import time
from datetime import datetime

from auth.kite import get_access_token, api_key
from kiteconnect import KiteConnect
from sqlalchemy import create_engine, text

# --- Configuration ---
DB_URI = os.environ.get("DATABASE_URI")  # e.g., "postgresql://user:password@host:port/db"
HIGH_VOLATILITY_THRESHOLD = 0.02  # Example: 2% price change over a short period
LOW_VOLUME_THRESHOLD = 1000  # Example: 1000 shares traded in the last minute


class OrderExecutor:
    def __init__(self):
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(get_access_token())
        self.db_engine = create_engine(DB_URI) if DB_URI else None

    def log_order_to_db(self, order_id, exchange_order_id, symbol, t_type, o_type, qty, price, status):
        """Logs an order to the database."""
        if not self.db_engine:
            logging.warning("Database engine not initialized. Skipping order logging.")
            return

        with self.db_engine.connect() as connection:
            stmt = text(
                """
                INSERT INTO orders (order_id, exchange_order_id, symbol, transaction_type, order_type, quantity, price, status, order_timestamp)
                VALUES (:order_id, :exchange_order_id, :symbol, :t_type, :o_type, :qty, :price, :status, :ts)
                """
            )
            connection.execute(stmt, {
                "order_id": order_id, "exchange_order_id": exchange_order_id, "symbol": symbol,
                "t_type": t_type, "o_type": o_type, "qty": qty, "price": price,
                "status": status, "ts": datetime.now()
            })

    def place_market_order(self, symbol: str, quantity: int, transaction_type: str):
        """Places a market order."""
        try:
            order_id = self.kite.place_order(
                tradingsymbol=symbol,
                exchange=self.kite.EXCHANGE_NSE,
                transaction_type=transaction_type,
                quantity=quantity,
                order_type=self.kite.ORDER_TYPE_MARKET,
                product=self.kite.PRODUCT_MIS, # Margin Intraday Squareoff
            )
            logging.info(f"Market order placed for {symbol}. Order ID: {order_id}")
            self.log_order_to_db(order_id, None, symbol, transaction_type, "MARKET", quantity, None, "PLACED")
            return order_id
        except Exception as e:
            logging.error(f"Failed to place market order for {symbol}: {e}")
            return None

    def place_limit_order(self, symbol: str, quantity: int, price: float, transaction_type: str):
        """Places a limit order."""
        try:
            order_id = self.kite.place_order(
                tradingsymbol=symbol,
                exchange=self.kite.EXCHANGE_NSE,
                transaction_type=transaction_type,
                quantity=quantity,
                price=price,
                order_type=self.kite.ORDER_TYPE_LIMIT,
                product=self.kite.PRODUCT_MIS,
            )
            logging.info(f"Limit order placed for {symbol} at {price}. Order ID: {order_id}")
            self.log_order_to_db(order_id, None, symbol, transaction_type, "LIMIT", quantity, price, "PLACED")
            return order_id
        except Exception as e:
            logging.error(f"Failed to place limit order for {symbol}: {e}")
            return None

    def place_twap_order(self, symbol: str, total_quantity: int, duration_minutes: int, transaction_type: str):
        """Places a TWAP order."""
        num_orders = duration_minutes
        if num_orders == 0:
            logging.error("TWAP duration must be at least 1 minute.")
            return []

        order_quantity = total_quantity // num_orders
        if order_quantity == 0:
            logging.error("Total quantity is too small for the given TWAP duration.")
            return []

        interval_seconds = (duration_minutes * 60) / num_orders
        order_ids = []

        for i in range(num_orders):
            order_id = self.place_market_order(symbol, order_quantity, transaction_type)
            if order_id:
                order_ids.append(order_id)
            if i < num_orders - 1:
                time.sleep(interval_seconds)

        return order_ids

    def execute_order(self, symbol: str, quantity: int, transaction_type: str, current_volume: int, current_volatility: float):
        """Chooses and executes the best order type based on market conditions."""
        if current_volatility > HIGH_VOLATILITY_THRESHOLD or current_volume < LOW_VOLUME_THRESHOLD:
            logging.info("High volatility or low volume detected. Using TWAP order.")
            # For simplicity, using a fixed 5-minute TWAP. A real system would have more dynamic logic.
            return self.place_twap_order(symbol, quantity, 5, transaction_type)
        else:
            logging.info("Market conditions are stable. Placing market order.")
            return self.place_market_order(symbol, quantity, transaction_type)
