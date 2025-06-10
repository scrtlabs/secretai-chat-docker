# Use official Python 3.12 slim image
FROM python:3.12-slim

# Set working dir
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source (main.py, static/, data/ etc.)
COPY . .

# Expose both ports: 8000 for FastAPI and 8501 only if you still have Streamlit
EXPOSE 8000

# Default command: launch Uvicorn with auto-reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]