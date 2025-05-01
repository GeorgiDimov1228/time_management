# Use an official lightweight Python image.
FROM python:3.9-slim

# Set the working directory in the container.
WORKDIR /app

# RUN apt-get update && apt-get install -y --no-install-recommends \
#     git \
#     # Add any other system dependencies your app needs here
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies.
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Expose port 8000 and run the FastAPI app with uvicorn.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
