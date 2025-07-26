# Use the official Python image.
FROM python:3.9-slim

# Set the working directory.
WORKDIR /app

# Copy requirements and install dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the necessary application code.
COPY ingestion/ ./ingestion
COPY common/ ./common
COPY auth/ ./auth # For getting access tokens

# Command to run the application.
CMD ["python", "-m", "ingestion.streamer"]
