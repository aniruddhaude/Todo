import streamlit as st
import os
import datetime
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
from openai import OpenAI

from auth import login_screen, BRANCHES
from db import (
    get_db,
    add_task, get_tasks, update_task, delete_task,
    mark_completed,
    mark_attendance, get_attendance, get_attendance_report,
    get_all_users,
    get_performance,
    add_library_item, get_library_items, delete_library_item,
    hash_password
)

st.set_page_config(page_title="Todo Planner", page_icon="📚", layout="wide")

load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

os.makedirs("submissions", exist_ok=True)
os.makedirs("library_files", exist_ok=True)
os.makedirs("profile_photos", exist_ok=True)


def init():
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "view" not in st.session_state:
        st.session_state.view = "Dashboard"

init()


st.markdown("""
<style>

.fade-container {animation: fadein .12s ease-out;}
@keyframes fadein {from{opacity:0;transform:translateY(2px);}to{opacity:1;transform:translateY(0);}}

/* active tab highlight */
.sidebar-active {background:#e6ebff !important;border-left:4px solid #304ffe;}

/* compact sidebar buttons */
section[data-testid="stSidebar"] button {width:100% !important;border-radius:6px;padding:4px 0;margin-bottom:1px;}
section[data-testid="stSidebar"] div[data-testid="stButton"] {margin-bottom:2px !important;}

</style>
""", unsafe_allow_html=True)


def send_email(to, subject, message):
    if not EMAIL_USER or not EMAIL_PASS:
        return
    msg = MIMEText(message)
    msg["Subject"], msg["From"], msg["To"] = subject, EMAIL_USER, to
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, to, msg.as_string())


# ---------------- PROFILE ----------------
def profile_page():
    user = st.session_state.current_user
    conn = get_db()

    st.subheader("My Profile")

    if user.get("photo_path"):
        st.image(user["photo_path"], width=140)

    name = st.text_input("Full Name", user["name"])
    phone = st.text_input("Mobile", user.get("phone", ""))
    dob = st.text_input("Date of Birth", user.get("dob", ""))

    photo = st.file_uploader("Change Photo", type=["png","jpg","jpeg"])
    photo_path = user.get("photo_path")

    if photo:
        save = f"profile_photos/{user['email']}.png"
        with open(save, "wb") as f:
            f.write(photo.read())
        photo_path = save

    if st.button("Save Profile"):
        conn.execute(
            "UPDATE users SET name=?, phone=?, dob=?, photo_path=? WHERE id=?",
            (name, phone, dob, photo_path, user["id"])
        )
        conn.commit()
        user.update({"name": name, "phone": phone, "dob": dob, "photo_path": photo_path})
        st.success("Profile updated")
        st.rerun()


# ---------------- DASHBOARD ----------------
def dashboard():
    user = st.session_state.current_user
    conn = get_db()

    st.subheader("Tasks")

    # ---------- TEACHER ----------
    if user["role"] == "teacher":
        title = st.text_input("Task Title")
        desc = st.text_area("Description")
        deadline = st.date_input("Deadline")
        assign_type = st.radio("Assign To", ["Student","Branch"])

        students = conn.execute(
            "SELECT id,name,branch FROM users WHERE role='student'"
        ).fetchall()

        if assign_type == "Student":
            s = st.selectbox(
                "Student",
                [(x["id"], f"{x['name']} — {x['branch']}") for x in students],
                format_func=lambda x: x[1]
            )
            assigned_to = f"student:{s[0]}"
        else:
            b = st.selectbox("Branch", BRANCHES)
            assigned_to = f"branch:{b}"

        if st.button("Assign Task"):
            add_task(title, desc, str(deadline), assigned_to, user["id"])
            st.success("Task assigned")

        st.divider()

        # ---------- ATTENDANCE MANAGER ----------
        st.subheader("Attendance Manager")

        students = conn.execute(
            "SELECT id, name, branch FROM users WHERE role='student'"
        ).fetchall()

        # FIX: convert sqlite3.Row -> dict (prevents pickle error)
        students = [dict(s) for s in students]

        selected_student = st.selectbox(
            "Select student",
            students,
            format_func=lambda s: f"{s['name']} — {s['branch']}"
        )

        if st.button("Mark Today's Attendance"):
            mark_attendance(selected_student["id"])
            st.success("Attendance recorded")

        st.divider()
        st.subheader("All Tasks")

        for t in get_tasks():
            with st.expander(f"{t['title']} — {t['deadline']}"):
                et = st.text_input("Edit title", t["title"], key=f"et{t['id']}")
                ed = st.text_area("Edit desc", t["description"], key=f"ed{t['id']}")
                dl = st.date_input(
                    "Edit deadline",
                    datetime.date.fromisoformat(t["deadline"]),
                    key=f"dl{t['id']}"
                )

                if st.button("Save", key=f"s{t['id']}"):
                    update_task(t["id"], et, ed, str(dl))
                    st.success("Updated")

                if st.button("Delete", key=f"d{t['id']}"):
                    delete_task(t["id"])
                    st.warning("Deleted")
                    st.rerun()

                if t["pdf_path"]:
                    with open(t["pdf_path"],"rb") as f:
                        st.download_button("Download submission", f, key=f"dw{t['id']}")

    # ---------- STUDENT ----------
    if user["role"] == "student":
        tasks = [
            t for t in get_tasks()
            if t["assigned_to"] == f"student:{user['id']}"
            or t["assigned_to"] == f"branch:{user['branch']}"
        ]

        for t in tasks:
            with st.expander(f"{t['title']} — {t['deadline']}"):
                folder = f"submissions/{user['id']}"
                os.makedirs(folder, exist_ok=True)

                upload = st.file_uploader("Upload PDF", type=["pdf"], key=f"u{t['id']}")
                if upload:
                    save = f"{folder}/{t['id']}.pdf"
                    with open(save,"wb") as f:
                        f.write(upload.read())
                    conn.execute("UPDATE tasks SET pdf_path=? WHERE id=?", (save,t["id"]))
                    conn.commit()
                    st.success("Uploaded")

                if st.button("Complete", key=f"c{t['id']}"):
                    mark_completed(user["id"], t["id"])
                    st.success("Marked complete")

        st.divider()

        # ---------- ATTENDANCE VIEW (READ ONLY) ----------
        st.subheader("Attendance (CodeChef Style)")

        records = get_attendance(user["id"])
        attended = {r["date"] for r in records}

        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=365)

        days = []
        d = start_date
        while d <= today:
            days.append(d)
            d += datetime.timedelta(days=1)

        st.write("Last 12 months")

        cols = st.columns(53)

        for i, col in enumerate(cols):
            with col:
                week_days = days[i*7:(i+1)*7]
                for wd in week_days:
                    iso = wd.isoformat()

                    style = (
                        "background-color:#2e7d32;"
                        if iso in attended
                        else "background-color:#d7d7d7;"
                    )

                    st.markdown(
                        f"<div style='{style} width:14px; height:14px; border-radius:3px; margin:2px;'></div>",
                        unsafe_allow_html=True,
                    )

        percent = round((len(attended) / 365) * 100, 1)
        st.metric("Attendance (Year)", f"{percent}%")


# ---------------- PERFORMANCE ----------------
def performance():
    st.subheader("Task Performance")
    st.dataframe(get_performance())
    st.subheader("Attendance Report")
    st.dataframe(get_attendance_report())


# ---------------- LIBRARY ----------------
def library_page():
    user = st.session_state.current_user
    st.subheader("Library")

    conn = get_db()

    if user["role"] == "teacher":
        title = st.text_input("PDF Title")
        desc = st.text_area("Description")
        branch = st.selectbox("Visible To (Branch)", ["ALL"] + BRANCHES)
        upload = st.file_uploader("Upload PDF", type=["pdf"])

        if st.button("Upload PDF"):
            if upload:
                path = f"library_files/{upload.name}"
                with open(path, "wb") as f:
                    f.write(upload.read())

                add_library_item(title, desc, path, user["id"], branch)
                st.success("PDF added to Library.")
                st.rerun()

        st.divider()

    st.subheader("Available Library Files")

    search = st.text_input("Search library...")

    items = get_library_items(
        user["branch"] if user["role"] == "student" else None
    )

    if search:
        items = [i for i in items if search.lower() in i["title"].lower()]

    if not items:
        st.info("No files found.")
        return

    for item in items:
        file_size = os.path.getsize(item["file_path"]) // 1024
        uploader = conn.execute(
            "SELECT name FROM users WHERE id=?",
            (item["uploaded_by"],)
        ).fetchone()

        uploader_name = uploader["name"] if uploader else "Unknown"

        with st.expander(f"{item['title']}  |  {file_size} KB"):
            st.write(item["description"])
            st.write(f"Uploaded by: **{uploader_name}**")
            st.write(f"Date: {item['uploaded_at']}")
            st.write(f"Branch: {item['branch']}")

            with open(item["file_path"], "rb") as f:
                st.download_button("Download", f)

            if user["role"] == "teacher":
                if st.button("Delete", key=f"del_{item['id']}"):
                    delete_library_item(item["id"])
                    st.warning("File removed")
                    st.rerun()


# ---------------- ADMIN ----------------
def admin_panel():
    conn = get_db()
    st.subheader("Manage Students")

    for u in get_all_users():
        if u["role"] == "student":
            with st.expander(f"{u['name']} — {u['email']}"):
                name = st.text_input("Name", u["name"], key=f"nm{u['id']}")
                email = st.text_input("Email", u["email"], key=f"em{u['id']}")
                branch = st.selectbox(
                    "Branch", BRANCHES,
                    index=BRANCHES.index(u["branch"]),
                    key=f"br{u['id']}"
                )
                phone = st.text_input(
                    "Phone",
                    u["phone"] if "phone" in u.keys() and u["phone"] else "",
                    key=f"ph{u['id']}"
                )
                pw = st.text_input("Reset Password", type="password", key=f"pw{u['id']}")

                if st.button("Save", key=f"sv{u['id']}"):
                    if pw:
                        hashed = hash_password(pw)
                        conn.execute(
                            "UPDATE users SET name=?,email=?,branch=?,phone=?,password=? WHERE id=?",
                            (name,email,branch,phone,hashed,u["id"])
                        )
                    else:
                        conn.execute(
                            "UPDATE users SET name=?,email=?,branch=?,phone=? WHERE id=?",
                            (name,email,branch,phone,u["id"])
                        )
                    conn.commit()
                    st.success("Updated")


# ---------------- CHAT SUPPORT ----------------
def chat_support():
    st.subheader("Support Assistant")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    for m in st.session_state.chat:
        st.write(m)

    q = st.text_input("Ask something:")
    if st.button("Send"):
        st.session_state.chat.append(f"Student: {q}")
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":q}]
        )
        ans = res.choices[0].message.content
        st.session_state.chat.append(f"Assistant: {ans}")
        st.rerun()


# ---------------- LAYOUT ----------------
def main_layout():
    st.sidebar.image("rcpit_logo.png", width=180)

    st.sidebar.markdown(
        "<h4 style='text-align:center; margin-top:-8px;'>RCPIT Shirpur</h4>",
        unsafe_allow_html=True
    )

    st.sidebar.write("---")

    menu = ["Dashboard", "Profile", "Library", "Help Chat"]

    if st.session_state.current_user["role"] == "teacher":
        menu += ["Performance", "Admin"]

    menu += ["Logout"]

    for page in menu:
        active = "sidebar-active" if page == st.session_state.view else ""
        st.sidebar.markdown(f'<div class="{active}">', unsafe_allow_html=True)

        if st.sidebar.button(page, key=f"nav_{page}", use_container_width=True):
            if page == "Logout":
                st.session_state.current_user = None
                st.rerun()
            else:
                st.session_state.view = page
                st.rerun()

    st.markdown('<div class="fade-container">', unsafe_allow_html=True)

    match st.session_state.view:
        case "Dashboard": dashboard()
        case "Profile": profile_page()
        case "Library": library_page()
        case "Performance": performance()
        case "Admin": admin_panel()
        case "Help Chat": chat_support()

    st.markdown('</div>', unsafe_allow_html=True)


# ---------------- ENTRY ----------------
if st.session_state.current_user:
    main_layout()
else:
    login_screen()
