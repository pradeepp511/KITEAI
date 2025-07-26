import json
import logging
import time

from google.cloud import pubsub_v1
from kiteconnect import KiteTicker

from auth.kite import get_access_token, api_key
from ingestion.config import INSTRUMENT_TOKENS, PROJECT_ID, TOPIC_ID

logging.basicConfig(level=logging.INFO)


class Streamer:
    def __init__(self):
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(PROJECT_ID, TOPIC_ID)
        self.kws = None
        self.access_token = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5  # seconds

    def start_streaming(self):
        self.access_token = get_access_token()
        self.kws = KiteTicker(api_key=api_key, access_token=self.access_token)
        self.kws.on_ticks = self.on_ticks
        self.kws.on_connect = self.on_connect
        self.kws.on_close = self.on_close
        self.kws.on_error = self.on_error

        while True:
            if not self.is_connected:
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    logging.info("Attempting to connect...")
                    self.kws.connect(threaded=False) # Blocking call
                else:
                    logging.error("Maximum reconnect attempts reached. Exiting.")
                    break

            # If connection drops, on_close will set is_connected to False,
            # and the loop will attempt to reconnect after a delay.
            if not self.is_connected:
                self.reconnect_attempts += 1
                delay = self.reconnect_delay * (2 ** (self.reconnect_attempts - 1))
                logging.info(f"Attempting to reconnect in {delay} seconds (Attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})...")
                time.sleep(delay)


    def on_ticks(self, ws, ticks):
        logging.info(f"Received {len(ticks)} ticks.")
        for tick in ticks:
            message = json.dumps(tick).encode("utf-8")
            future = self.publisher.publish(self.topic_path, message)
            future.add_done_callback(lambda f: logging.debug(f"Published message with ID: {f.result()}"))

    def on_connect(self, ws, response):
        logging.info("WebSocket connection established.")
        self.is_connected = True
        self.reconnect_attempts = 0
        logging.info(f"Subscribing to tokens: {INSTRUMENT_TOKENS}")
        ws.subscribe(INSTRUMENT_TOKENS)
        ws.set_mode(ws.MODE_FULL, INSTRUMENT_TOKENS)

    def on_close(self, ws, code, reason):
        logging.warning(f"WebSocket connection closed. Code: {code}, Reason: {reason}")
        self.is_connected = False

    def on_error(self, ws, code, reason):
        logging.error(f"WebSocket error. Code: {code}, Reason: {reason}")
        # on_close will be called next, which will handle the reconnect logic.


if __name__ == "__main__":
    streamer = Streamer()
    streamer.start_streaming()
