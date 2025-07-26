import argparse
import logging
from datetime import datetime

import apache_beam as beam
from apache_beam.io.jdbc import WriteToJdbc
from apache_beam.options.pipeline_options import PipelineOptions

from auth.kite import get_access_token, api_key
from kiteconnect import KiteConnect


class HistoricalDataOptions(PipelineOptions):
    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument('--instrument_tokens', required=True, help='Comma-separated list of instrument tokens')
        parser.add_argument('--from_date', required=True, help='From date in YYYY-MM-DD format')
        parser.add_argument('--to_date', required=True, help='To date in YYYY-MM-DD format')
        parser.add_argument('--db_host', required=True, help='Database host')
        parser.add_argument('--db_port', required=True, help='Database port')
        parser.add_argument('--db_name', required=True, help='Database name')
        parser.add_argument('--db_user', required=True, help='Database user')
        parser.add_argument('--db_password', required=True, help='Database password')
        parser.add_argument('--jdbc_driver_jar', required=True, help='Path to the PostgreSQL JDBC driver JAR')


class FetchHistoricalData(beam.DoFn):
    def __init__(self, from_date, to_date):
        self.from_date = from_date
        self.to_date = to_date
        self.kite = None

    def setup(self):
        access_token = get_access_token()
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)

    def process(self, instrument_token):
        logging.info(f"Fetching data for instrument token: {instrument_token}")

        # Fetch 1-minute data
        records_1min = self.kite.historical_data(instrument_token, self.from_date, self.to_date, "minute", continuous=True)
        for r in records_1min:
            yield beam.pvalue.TaggedOutput('1min', {
                "time": r['date'].isoformat(),
                "instrument_token": instrument_token,
                "open": r['open'],
                "high": r['high'],
                "low": r['low'],
                "close": r['close'],
                "volume": r['volume']
            })

        # Fetch EOD data
        records_eod = self.kite.historical_data(instrument_token, self.from_date, self.to_date, "day", continuous=True)
        for r in records_eod:
            yield beam.pvalue.TaggedOutput('eod', {
                "time": r['date'].isoformat(),
                "instrument_token": instrument_token,
                "open": r['open'],
                "high": r['high'],
                "low": r['low'],
                "close": r['close'],
                "volume": r['volume']
            })


def run():
    pipeline_options = PipelineOptions()
    p = beam.Pipeline(options=pipeline_options)
    custom_options = pipeline_options.view_as(HistoricalDataOptions)

    instrument_tokens = [int(token) for token in custom_options.instrument_tokens.split(',')]

    db_url = f"jdbc:postgresql://{custom_options.db_host}:{custom_options.db_port}/{custom_options.db_name}"

    # Main pipeline
    results = (
        p
        | 'CreateTokens' >> beam.Create(instrument_tokens)
        | 'FetchData' >> beam.ParDo(FetchHistoricalData(custom_options.from_date, custom_options.to_date)).with_outputs('1min', 'eod')
    )

    # Write 1-minute data to DB
    ( results['1min']
        | 'ConvertToRow1min' >> beam.Map(lambda x: beam.Row(**x))
        | 'Write1MinToDB' >> WriteToJdbc(
            driver_class_name='org.postgresql.Driver',
            jdbc_url=db_url,
            username=custom_options.db_user,
            password=custom_options.db_password,
            table_name='ohlcv_1min',
            driver_jars=custom_options.jdbc_driver_jar
        )
    )

    # Write EOD data to DB
    ( results['eod']
        | 'ConvertToRowEod' >> beam.Map(lambda x: beam.Row(**x))
        | 'WriteEODToDB' >> WriteToJdbc(
            driver_class_name='org.postgresql.Driver',
            jdbc_url=db_url,
            username=custom_options.db_user,
            password=custom_options.db_password,
            table_name='ohlcv_eod',
            driver_jars=custom_options.jdbc_driver_jar
        )
    )

    result = p.run()
    result.wait_until_finish()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
