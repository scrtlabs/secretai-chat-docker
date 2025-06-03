# Use the official Python 3.12 slim image as a base
FROM python:3.12-slim

# Set working directory inside the container to /app
WORKDIR /app

# Copy only the requirements file first to leverage Docker layer caching;
# then install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code (including app_streamlit.py)
# into /app
COPY . .

# Expose Streamlit’s default port so it can be accessed externally
EXPOSE 8501

# When the container starts, run Streamlit directly.
# It will look for app_streamlit.py in /app.
CMD ["streamlit", "run", "app_streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"]
