#!/bin/bash

# This script runs the historical data ingestion pipeline on Google Cloud Dataflow.

# --- Configuration ---
PROJECT_ID="kite-trader"
REGION="us-central1"
BUCKET="gs://kite-trader-dataflow" # Replace with your GCS bucket for staging
SUBNET="default" # Replace with your VPC subnet if needed

# Database connection details (replace with your actual credentials)
DB_HOST="your_db_host"
DB_PORT="5432"
DB_NAME="your_db_name"
DB_USER="your_db_user"
DB_PASSWORD="your_db_password"

# Path to the PostgreSQL JDBC driver JAR.
# Download from: https://jdbc.postgresql.org/download.html
# Upload it to a GCS bucket to make it accessible to Dataflow workers.
JDBC_DRIVER_JAR="gs://kite-trader-dataflow/jars/postgresql-42.6.0.jar"

# Pipeline parameters
INSTRUMENT_TOKENS="256265,260105" # Example: NIFTY 50, NIFTY BANK
FROM_DATE="2023-01-01"
TO_DATE="2023-01-31"

# --- Runner ---
python -m ingestion.historical \
    --runner DataflowRunner \
    --project $PROJECT_ID \
    --region $REGION \
    --temp_location $BUCKET/temp \
    --staging_location $BUCKET/staging \
    --subnet "regions/$REGION/subnetworks/$SUBNET" \
    --instrument_tokens $INSTRUMENT_TOKENS \
    --from_date $FROM_DATE \
    --to_date $TO_DATE \
    --db_host $DB_HOST \
    --db_port $DB_PORT \
    --db_name $DB_NAME \
    --db_user $DB_USER \
    --db_password $DB_PASSWORD \
    --jdbc_driver_jar $JDBC_DRIVER_JAR \
    --experiments=use_fast_coders
