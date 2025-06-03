#!/usr/bin/env bash
set -e

# Ensure /app/data directory exists (mounted from host)
if [ ! -d /app/data ]; then
  mkdir -p /app/data
fi

# If history.json doesn’t exist, create it as an empty JSON array
if [ ! -f /app/data/history.json ]; then
  echo "[]" > /app/data/history.json
fi

# Run Streamlit
exec streamlit run app_streamlit.py --server.port=8501 --server.address=0.0.0.0