#!/usr/bin/env bash
set -e

# If history.json does not exist in /app, create it with an empty JSON array.
# Because /app is bind-mounted to the host project directory, this will also
# create history.json on the host automatically.
if [ ! -f /app/history.json ]; then
  echo "[]" > /app/history.json
fi

# Execute Streamlit, binding to all network interfaces on port 8501.
exec streamlit run app_streamlit.py --server.port=8501 --server.address=0.0.0.0
