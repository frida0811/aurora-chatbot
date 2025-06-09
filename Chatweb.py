import streamlit as st
from openai import OpenAI
from datetime import datetime
import pyperclip
import hashlib
import os
import json
import textract
from PyPDF2 import PdfReader
import docx2txt

# Initialize OpenAI client, assuming the API key is set via environment variable or other means
client = OpenAI(
    api_key="sk-aurora-hn9sauHQ5RddXlIY7MdwT3BlbkFJUIKnlW6QhKBPF40ZGbe6"
)

USER_DATA_FILE = "user_data.json"

# Load user data
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# Save user data
def save_user_data(user_data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f)

# Load user data into session state
if 'users' not in st.session_state:
    st.session_state.users = load_user_data()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'current_conversation' not in st.session_state:
    st.session_state.current_conversation = None
if 'likes' not in st.session_state:
    st.session_state.likes = {}  # Track likes
if 'copied' not in st.session_state:
    st.session_state.copied = False  # Track copy status

# User registration function
def register_user(username):
    if username in st.session_state.users:
        return False
    st.session_state.users[username] = {
        "conversations": {}
    }
    save_user_data(st.session_state.users)
    return True

# User login function
def login_user(username):
    if username in st.session_state.users:
        st.session_state.logged_in = True
        st.session_state.current_user = username
        return True
    return False

# Handle uploaded file
def handle_uploaded_file(uploaded_file):
    file_extension = uploaded_file.name.split(".")[-1].lower()
    if file_extension == "txt":
        return uploaded_file.read().decode("utf-8")
    elif file_extension == "pdf":
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    elif file_extension in ["doc", "docx"]:
        text = docx2txt.process(uploaded_file)
        return text
    else:
        st.error("Unsupported file type")
        return ""

# User registration and login interface
if not st.session_state.logged_in:
    st.sidebar.image("logo.png", use_column_width=True)  # Replace with your logo file path
    st.sidebar.title('Project Name: Aurora')  # Replace with your project name

    st.sidebar.title("User Registration and Login")
    option = st.sidebar.selectbox("Select Action", ["Register", "Login"])

    if option == "Register":
        username = st.sidebar.text_input("Username")
        if st.sidebar.button("Register"):
            if register_user(username):
                st.sidebar.success("Registration successful, please login")
            else:
                st.sidebar.error("Username already exists")

    elif option == "Login":
        username = st.sidebar.text_input("Username")
        if st.sidebar.button("Login"):
            if login_user(username):
                st.sidebar.success("Login successful")
            else:
                st.sidebar.error("Username not found")

else:
    # Display user avatar and username
    st.sidebar.image("logo.png", width=100)  # Replace with your logo file path and set width
    st.sidebar.write(f"{st.session_state.current_user}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.current_conversation = None

def handle_conversation(messages):
    # 使用GPT-4模型并开启流式响应
    stream = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        stream=True,
    )

    response_text = ""
    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            response_text += chunk.choices[0].delta.content
    return response_text

# Streamlit UI
st.markdown(
    """
    <style>
    * {
        font-family: 'Times New Roman', Times, serif;
    }
    h1, h2, h3, h4, h5, h6, .stSidebar, .stButton, .stTextInput {
        font-family: 'Times New Roman', Times, serif;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title('Aurora')

if st.session_state.logged_in:
    current_user = st.session_state.current_user
    user_data = st.session_state.users[current_user]

    # Custom CSS
    st.markdown(
        """
        <style>
        .sidebar-button {
            width: 100%;
            margin-bottom: 10px;
        }
        .btn-container {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        .btn-like {
            font-size: 24px;
            cursor: pointer;
            border: none;
            background: none;
            padding: 0;
            outline: none;
        }
        .btn-like.liked {
            color: red;
        }
        .btn-like.not-liked {
            color: grey;
        }
        </style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
        """,
        unsafe_allow_html=True
    )

    # Sidebar features
    with st.sidebar:
        st.header("Conversation Management")

        # Display current conversation
        st.write(f"Current Conversation: {st.session_state.current_conversation}")

        # New conversation
        new_conversation_name = st.text_input("New Conversation Name")
        if st.button("Create New Conversation"):
            if new_conversation_name:
                user_data["conversations"][new_conversation_name] = []
                st.session_state.current_conversation = new_conversation_name

        # Switch conversation buttons
        for conversation in user_data["conversations"].keys():
            if st.button(conversation, key=f"conv_{conversation}", help=conversation, use_container_width=True):
                st.session_state.current_conversation = conversation

    # Display conversation history in a separate text area
    # st.write("Conversation History:")
    conversation_history = ""
    for msg in user_data["conversations"].get(st.session_state.current_conversation, []):
        role = "You" if msg["role"] == "user" else "Aurora"
        message_text = f"{msg['timestamp']} - {role}: {msg['content']}"
        conversation_history += message_text + "\n"
    st.text_area("Conversation History", conversation_history, height=300)

    # Multi-line text input for user message
    user_input = st.text_area("Enter your message:", key="user_input")

    # File upload
    uploaded_file = st.file_uploader("Upload Document", type=["pdf", "doc", "docx", "txt"])
    file_content = ""
    if uploaded_file is not None:
        file_content = handle_uploaded_file(uploaded_file)
        st.text_area("File Content", file_content, height=200)  # Display file content (text format)

    # Button container
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button('Send'):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_conversation = st.session_state.current_conversation

            # If current conversation does not exist, create a "New Chat" conversation
            if current_conversation is None:
                current_conversation = "New Chat"
                if current_conversation not in user_data["conversations"]:
                    user_data["conversations"][current_conversation] = []
                st.session_state.current_conversation = current_conversation

            # Merge text input and file content
            combined_input = user_input + "\n" + file_content

            user_message = {"role": "user", "content": combined_input}
            user_data["conversations"][current_conversation].append(
                {"role": "user", "content": combined_input, "timestamp": timestamp})

            # Prepare messages to be sent
            messages = [{"role": "system", "content": "You are a helpful assistant."}] + [
                {"role": m["role"], "content": m["content"]} for m in user_data["conversations"][current_conversation]
            ]

            response = handle_conversation(messages)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_data["conversations"][current_conversation].append(
                {"role": "assistant", "content": response, "timestamp": timestamp})
            st.session_state.likes[response] = False  # Initialize like status to False
            st.session_state.copied = False  # Reset copy status
            save_user_data(st.session_state.users)  # Save updated data
            st.experimental_rerun()

    with col2:
        if st.button('Clear Conversation History'):
            user_data["conversations"][st.session_state.current_conversation] = []
            save_user_data(st.session_state.users)
            st.experimental_rerun()

    with col3:
        if st.button('Export Conversation History'):
            history_text = ""
            for message in user_data["conversations"].get(st.session_state.current_conversation, []):
                role = "You" if message["role"] == "user" else "Aurora"
                history_text += f"{message['timestamp']} - {role}: {message['content']}\n"
            st.download_button('Download Conversation History', history_text,
                               file_name=f'{st.session_state.current_conversation}_conversation_history.txt')

    # Display messages with actions
    st.write("Actions:")
    for message in user_data["conversations"].get(st.session_state.current_conversation, []):
        if message["role"] == "assistant":
            liked = st.session_state.likes.get(message['content'], False)
            like_class = "btn-like liked" if liked else "btn-like not-liked"

            col1, col2 = st.columns([10, 1])
            with col1:
                st.write(f"{message['timestamp']} - Aurora: {message['content']}")
            with col2:
                if st.button(f"Copy", key="copy_" + message["timestamp"]):
                    pyperclip.copy(message["content"])
                    st.session_state.copied = True
                    st.session_state.likes[message['content']] = True  # Auto-like
                    st.success('Content copied to clipboard')
                    st.experimental_rerun()

                st.markdown(
                    f"""
                    <div class="btn-container">
                        <span class="{like_class}">
                            <i class="fa fa-thumbs-up"></i>
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

else:
    st.write("Please log in to use the conversation assistant.")
