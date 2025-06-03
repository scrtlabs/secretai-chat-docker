import os
import json
import streamlit as st
from secret_ai_sdk.secret import Secret
from secret_ai_sdk.secret_ai import ChatSecret
import nest_asyncio
# Apply nest_asyncio to allow asyncio loop in Streamlit's thread
nest_asyncio.apply()

# Load API key
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    st.error("Set API_KEY environment variable")
    st.stop()

# Initialize Secret client and select model
os.environ["SECRET_AI_API_KEY"] = API_KEY
secret_client = Secret()
models = secret_client.get_models()
if not models:
    st.error("No models available from Secret AI SDK")
    st.stop()
MODEL = models[0]
urls = secret_client.get_urls(model=MODEL)
if not urls:
    st.error(f"No URLs available for model {MODEL}")
    st.stop()
BASE_URL = urls[0]

# Set up ChatSecret LLM
llm = ChatSecret(base_url=BASE_URL, model=MODEL, temperature=1.0)

# History file and session state
HISTORY_FILE = os.path.join(os.getcwd(), 'history.json')
if 'history' not in st.session_state:
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w') as f:
            json.dump([], f)
    with open(HISTORY_FILE, 'r') as f:
        st.session_state.history = json.load(f)

# UI title
st.title("Secret AI Chat (Streamlit)")

# Display existing chat history
for role, text in st.session_state.history:
    st.chat_message(role).write(text)

# Chat input
user_input = st.chat_input("Enter message...")
if user_input:
    # Show user message
    st.chat_message('user').write(user_input)
    st.session_state.history.append(("user", user_input))

    # Prepare messages for LLM
    messages = [
        {"role": role, "content": text}
        for role, text in st.session_state.history
    ]
    # Call ChatSecret chat endpoint
    response = llm.invoke(messages)
    assistant_msg = response.content

    # Display assistant's message
    st.chat_message('assistant').write(assistant_msg)
    st.session_state.history.append(("assistant", assistant_msg))

    # Save updated history
    with open(HISTORY_FILE, 'w') as f:
        json.dump(st.session_state.history, f, indent=2)