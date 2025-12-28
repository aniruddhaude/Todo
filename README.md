College Task & Learning Planner (Streamlit)

A role-based planner for colleges where:

Teachers create tasks, upload study material, track submissions, manage students.

Students view tasks, upload PDF submissions, track performance, track attendance.

Admin edits users and manages the system.

Includes:

Task dashboard

Attendance tracking

Student performance analytics

Library (with search, upload, file history, roles, timestamps)

Profile editing (photo, details)

Chat support

Email alerts (optional)

Built using Python + Streamlit + SQLite.

#Features
#Teacher

Create tasks (branch-wise or student-wise)

Download submissions

Track performance & attendance

Upload library PDFs (branch-specific or global)

Delete uploaded files

Edit student profiles (admin tools)

#Student

View assigned tasks

Upload submissions (PDF)

View completion records

See attendance calendar + percentage

Access library resources (branch-filtered)

Edit profile

🛠 Admin

Manage students

Reset passwords

Update branches and details

#Library Enhancements

Search bar

File size display

Uploaded by

Uploaded date/time

Delete (teacher only)

Branch-controlled visibility

📂 Project Structure
project/
│ app.py
│ auth.py
│ db.py
│ requirements.txt
│ README.md
│ planner.db        (auto created)
│
├── library_files/
├── submissions/
├── profile_photos/
└── rcpit_logo.png


Empty folders should be committed with a .gitkeep.

! Installation (Local)
1️⃣ Clone the repository
git clone https://github.com/yourname/college-planner.git
cd college-planner

2️⃣ Create virtual environment (recommended)
python -m venv venv
source venv/Scripts/activate   # Windows
source venv/bin/activate       # Mac/Linux

3️⃣ Install dependencies

Create requirements.txt (if not present) and add:

streamlit
pandas
python-dotenv
openai


Install:

pip install -r requirements.txt

4️⃣ Run the app
streamlit run app.py


Open the browser link shown.

 Environment Variables (optional but recommended)

Create .env:

EMAIL_USER=yourgmail@gmail.com
EMAIL_PASS=your-app-password
OPENAI_API_KEY=your-openai-key


To send emails, generate a Gmail App Password
(Google → Security → App Passwords).

 Database

Uses SQLite automatically:

Creates planner.db

Creates all tables

No manual setup needed

Tables include:

users

tasks

completed

attendance

library

🌐 Deployment — Streamlit Cloud
1️⃣ Push code to GitHub

Include:

app.py
auth.py
db.py
requirements.txt
rcpit_logo.png


Commit empty folders too.

2️⃣ Go to Streamlit Cloud
https://share.streamlit.io/


Click:

New App → Deploy from GitHub


Select repo and set:

Main file: app.py


Deploy.

3️⃣ Add Secrets (Environment Variables)

In Streamlit app → Settings → Secrets

EMAIL_USER = "yourgmail@gmail.com"
EMAIL_PASS = "your-app-password"
OPENAI_API_KEY = "your-openai-key"


Save.

App restarts automatically.

🧪 Testing Checklist

Teacher:

Create a task

Upload PDF to Library

Delete test files

Check performance dashboard

Student:

Upload submission

View assigned tasks

Track attendance calendar

Access Library resources

Admin:

Edit student info

Reset passwords

⚠️ Notes

Keep PDFs < 30MB

SQLite data persists on Streamlit Cloud

Gmail MUST use App Passwords (not your login)

For heavy usage, upgrade later to PostgreSQL + S3

🎯 Future Enhancements (optional ideas)

PDF preview without downloading

Version history for uploads

Student download tracking

Push notifications

HOD approval workflow

Analytics dashboard

🤝 Contributing

Pull requests are welcome.
Open an issue if something breaks — we improve together.