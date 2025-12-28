import streamlit as st
from db import get_user, get_db, hash_password

BRANCHES = [
    "Computer Science",
    "Artificial Intelligence and Machine Learning",
    "Artificial Intelligence and Data Science",
    "Data Science",
    "Information Technology",
    "Mechanical Engineering",
    "Civil Engineering",
    "Electrical Engineering",
    "Electronic and Telecommunication"
]


def login_screen():
    st.title("To-Do Planner RCPIT")

    tab1, tab2 = st.tabs(["Login", "Register"])

    # ------------------- LOGIN -------------------
    with tab1:
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")

        if st.button("Login"):
            user = get_user(email, pw)

            if not user:
                st.error("Invalid email or password")
            else:
                st.session_state.current_user = user
                st.success("Logged in successfully")
                st.rerun()

    # ------------------- REGISTER -------------------
    with tab2:
        name = st.text_input("Full Name", key="reg_name")
        reg_email = st.text_input("Register Email", key="reg_email")
        reg_pw = st.text_input("Create Password", type="password", key="reg_pw")
        role = st.radio("Role", ["student", "teacher"])
        branch = st.selectbox("Branch", BRANCHES)

        if st.button("Create Account"):
            if not name or not reg_email or not reg_pw:
                st.error("All fields are required")
            else:
                conn = get_db()

                try:
                    conn.execute(
                        "INSERT INTO users (name,email,password,role,branch) VALUES (?,?,?,?,?)",
                        (name, reg_email, hash_password(reg_pw), role, branch)
                    )
                    conn.commit()
                    st.success("Account created. You can login now.")
                except Exception as e:
                    st.error("Email already exists or invalid data.")
