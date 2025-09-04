import streamlit as st
import os
from dotenv import load_dotenv
from modified import pipeline, excel_to_mysql
load_dotenv()

# ----------------- Streamlit Config -----------------
st.set_page_config(page_title=" Operisoft Excel SQL Chat", layout="wide")
st.title("📊 Operisoft Excel Chat Assistant")

# Sidebar
st.sidebar.header("📂 Upload Excel File")
# Session State
if "table_names" not in st.session_state:
    st.session_state.table_names = []
if "loaded_files" not in st.session_state:
    st.session_state.loaded_files = []
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi 👋, I'm your assistant. Upload an Excel file and ask me anything!"}
    ]

# ----------------- File Upload -----------------
uploaded_file = st.sidebar.file_uploader("Upload Excel file", type=["xlsx"])
if uploaded_file:
    current_file = uploaded_file.name
    if st.session_state.loaded_files != [current_file]:
        # Reset chat
        st.session_state.messages = [
            {"role": "assistant", "content": f"New file `{uploaded_file.name}` uploaded ✅. Let's start fresh!"}
        ]

        # Save file
        path = os.path.join("temp", uploaded_file.name)
        os.makedirs("temp", exist_ok=True)
        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Load into MySQL
        table_names=excel_to_mysql(path)
        st.session_state.table_names = table_names
        st.session_state.loaded_files = [current_file]
        st.sidebar.success(f"✅ Loaded file: {uploaded_file.name}")

# ----------------- Chat History -----------------
st.markdown("---")
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").markdown(msg["content"])
    else:
        st.chat_message("assistant").markdown(msg["content"])

# ----------------- Chat Input -----------------
if query := st.chat_input("Ask a question about your Excel data..."):
    st.session_state.messages.append({"role": "user", "content": query})
    st.chat_message("user").markdown(query)

    with st.spinner("Thinking..."):
        try:
            print(st.session_state.table_names)
            response = pipeline(query) 
        except Exception as e:
            response = f"⚠️ Error: {str(e)}"

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").markdown(response)
