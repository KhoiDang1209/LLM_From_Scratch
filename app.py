import streamlit as st
import requests
from PIL import Image
import base64
import time

st.set_page_config(
    page_title="HCMIU Chatbot",
    page_icon="💬",
    layout="centered"
)

st.title("HCMIU Chatbot")
st.markdown("Hỏi đáp thông tin về trường Đại học Quốc tế")

API_URL = "https://f8a4-34-124-214-1.ngrok-free.app"

def get_chat_response(query):
    try:
        start_time = time.time()
        response = requests.post(
            f"{API_URL}/chat",
            json={"text": query},
            headers={"Content-Type": "application/json"}
        )
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
        
        if response.status_code == 200:
            raw_response = response.json().get("response", "")
            return extract_answer(raw_response), response_time
        else:
            return "Sorry, there was an error. Please try again.", response_time
    except Exception as e:
        return f"Error: {str(e)}", 0

def extract_answer(response_text):
    """Extract the answer part after [/INST]"""
    if "[/INST]" in response_text:
        return response_text.split("[/INST]", 1)[-1].strip()
    return response_text

if 'messages' not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        response, response_time = get_chat_response(prompt)
        st.markdown(response)
        st.caption(f"Response time: {response_time}ms")
        st.session_state.messages.append({"role": "assistant", "content": response}) 