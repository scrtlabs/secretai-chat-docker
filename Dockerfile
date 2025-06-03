# Use a minimal Python 3.12 image
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure history.json exists so that Streamlit can read/write it
RUN touch /app/history.json

# Expose Streamlit’s default port
EXPOSE 8501

# Run the Streamlit app on container start
CMD ["streamlit", "run", "app_streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"]