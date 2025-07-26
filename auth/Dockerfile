# Use the official Python image.
FROM python:3.9-slim

# Set the working directory.
WORKDIR /app

# Copy requirements and install dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the necessary application code.
COPY auth/ ./auth
COPY common/ ./common

# Expose the port the app runs on.
EXPOSE 8000

# Command to run the application.
CMD ["uvicorn", "auth.main:app", "--host", "0.0.0.0", "--port", "8000"]
