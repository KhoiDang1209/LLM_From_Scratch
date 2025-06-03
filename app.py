import streamlit as st
import requests

st.set_page_config(
    page_title="HCMIU Chatbot",
    page_icon="💬",
    layout="centered"
)

st.title("HCMIU Chatbot")
st.markdown("Hỏi đáp thông tin về trường Đại học Quốc tế")

API_URL = "https://7218-34-125-166-77.ngrok-free.app"

def get_chat_response(query):
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"text": query},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            raw_response = response.json().get("response", "")
            return extract_answer(raw_response)
        else:
            return "Sorry, there was an error. Please try again."
    except Exception as e:
        return f"Error: {str(e)}"

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
        response = get_chat_response(prompt)
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response}) 