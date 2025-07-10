import streamlit as st
import os
import bcrypt
import json
from pathlib import Path
from frontend import run_podwise_frontend

# ---------------------------
# 🔐 USER DATABASE FUNCTIONS
# ---------------------------
USER_DB_PATH = Path("users.json")
if not USER_DB_PATH.exists():
    with open(USER_DB_PATH, "w") as f:
        json.dump({"users": []}, f)

def load_users():
    with open(USER_DB_PATH) as f:
        return json.load(f)["users"]

def save_users(users):
    with open(USER_DB_PATH, "w") as f:
        json.dump({"users": users}, f, indent=2)

def authenticate(username, password):
    users = load_users()
    for user in users:
        if user["username"] == username:
            return bcrypt.checkpw(password.encode(), user["password"].encode())
    return False

def user_exists(username):
    return any(user["username"] == username for user in load_users())

def register_user(username, password):
    users = load_users()
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    users.append({"username": username, "password": hashed_pw})
    save_users(users)

# ---------------------------
# 🌐 STREAMLIT LOGIN PAGE
# ---------------------------
st.set_page_config(page_title="Podwise Login", layout="centered")

if not st.session_state.get("authenticated"):
    st.title("🔐 Welcome to Podwise")
    mode = st.radio("Select Mode", ["Login", "Sign Up"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if mode == "Login":
        if st.button("Login"):
            if authenticate(username, password):
                st.session_state["authenticated"] = True
                st.session_state["user"] = username
                st.rerun()
            else:
                st.error("Invalid username or password")

    elif mode == "Sign Up":
        confirm = st.text_input("Confirm Password", type="password")
        if st.button("Create Account"):
            if user_exists(username):
                st.warning("Username already exists.")
            elif password != confirm:
                st.error("Passwords do not match")
            elif not username or not password:
                st.warning("Enter both username and password")
            else:
                register_user(username, password)
                st.success("Account created! Please login.")
else:
    # ✅ User authenticated — run main app
    run_podwise_frontend()



# Add at the very end of auth_app.py or frontend.py
footer = """
    <style>
        .footer {
            position: fixed;
            bottom: 10px;
            left: 10px;
            font-size: 14px;
            color: gray;
            z-index: 100;
        }
    </style>
    <div class="footer">
        Created by: <strong>Khushi Batra</strong> • 
        <a href="https://github.com/khushi168" target="_blank">GitHub</a>
    </div>
"""
st.markdown(footer, unsafe_allow_html=True)

