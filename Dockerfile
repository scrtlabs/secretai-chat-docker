# Use the official Python 3.12 slim image as a base
FROM python:3.12-slim

# Set working directory inside the container to /app
WORKDIR /app

# Copy only the requirements file first to leverage Docker layer caching;
# install Python dependencies from requirements.txt
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy all application code into /app
COPY . .

# Expose Streamlit’s default port so it can be accessed externally
EXPOSE 8501

# Set entrypoint to our script. It will create history.json if missing,
# then start the Streamlit app.
ENTRYPOINT ["/app/entrypoint.sh"]
