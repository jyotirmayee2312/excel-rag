import streamlit as st
import os
import requests
from dotenv import load_dotenv
from urllib.parse import urlencode
# from dotenv import load_dotenv
from Excel_function import csv_to_sqlite, handle_user_question, db_name  

load_dotenv()

COGNITO_DOMAIN = "https://us-east-1hnq0jsedi.auth.us-east-1.amazoncognito.com"   # e.g., https://yourdomain.auth.ap-south-1.amazoncognito.com
CLIENT_ID = "66iq182l7gfjkh73enrs0ham4a"
# REDIRECT_URI = "http://localhost:6006/callback"
REDIRECT_URI = "https://chatwithexcel.operisoft.com/api/callback"
FASTAPI_BACKEND = "https://chatwithexcel.operisoft.com/api" # e.g., http://localhost:8000

# ---- Streamlit Session State ----
if "id_token" not in st.session_state:
    st.session_state.id_token = None

# ---- Check if token is passed in URL ----
st.set_page_config(page_title=" Operisoft Excel SQL Chat", layout="wide")
st.title("📊 Operisoft Excel Chat Assistant")

if "table_names" not in st.session_state:
    st.session_state.table_names = []
if "loaded_files" not in st.session_state:
    st.session_state.loaded_files = []
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi 👋, I'm your assistant. Upload an Excel file and ask me anything!"}
    ]

query_params = st.query_params
if "id_token" in query_params and not st.session_state.id_token:
    st.session_state.id_token = query_params["id_token"]

# ---- If no token, show login button ----
if not st.session_state.id_token:
    login_url = (
        f"{COGNITO_DOMAIN}/oauth2/authorize?"
        + urlencode({
            "response_type": "code",
            "client_id": CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "scope": "openid email phone"
        })  
    )
    st.markdown(f"### 🔑 [Login with Cognito]({login_url})")
    st.stop()

# ---- Verify token via FastAPI ----
if st.session_state.id_token:
    try:
        response = requests.get(
    f"{FASTAPI_BACKEND}/secure",
    headers={"Authorization": f"Bearer {st.session_state.id_token}"}
)
        if response.status_code != 200:
            st.error("❌ Authentication failed. Please login again.")
            st.session_state.id_token = None
            st.rerun()
        else:
            user_info = response.json()
            print("user_Info: ", user_info)

            st.sidebar.header("📂 Upload Excel File")
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

                    # Load into SQLite
                    table_names=csv_to_sqlite(path, db_name)
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
                        response = handle_user_question(query,st.session_state.table_names)  # 👈 call your SQL RAG handler
                    except Exception as e:
                        response = f"⚠️ Error: {str(e)}"

                st.session_state.messages.append({"role": "assistant", "content": response})
                st.chat_message("assistant").markdown(response)

            # st.success(f"✅ Logged in as {user_info.get('user').get('cognito:username')}")

    except Exception as e:
        st.error(f"⚠️ Auth check error: {e}")
        st.stop()
