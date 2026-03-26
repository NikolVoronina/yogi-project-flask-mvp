# 🌿 YOGI — Yoga Studio Web App

**Modern yoga booking system designed with a clean Scandinavian aesthetic and built using Flask, MariaDB, and Raspberry Pi.**

---

# 🚀 Overview

YOGI is a lightweight full-stack web application designed for small and mid-sized yoga studios.

The platform allows users to:

- Register and log in
- Browse weekly yoga schedules
- Book available classes
- View personal bookings
- Track upcoming and past classes

Administrators can:

- Access a protected admin panel
- View all bookings
- Manage studio activity

The project is optimized to run even on a **Raspberry Pi server**, making it suitable for small studios with minimal infrastructure.

---

# ✨ Features

### User System
- User registration
- Login / logout
- Secure password hashing
- Personal dashboard

### Booking System
- Class booking with limited spots
- Automatic seat counting
- Booking confirmation

### Schedule System
- Weekly schedule
- Dynamic class loading
- Category filtering

### Admin System
- Secure admin login
- Role-based access (`is_admin`)
- Protected routes
- Booking management

---

# 🛠 Tech Stack

## Backend

- Python 3
- Flask
- PyMySQL
- Werkzeug security

Key concepts used:

- session authentication
- decorators
- server-side rendering (Jinja2)

---

## Database

MariaDB / MySQL

Hosted locally on Raspberry Pi.

---

## Frontend

- HTML5
- CSS3
- Jinja2 Templates
- Figma → production UI

Design palette:


Primary green → #BAD341
Dark → #1E1E1E
Accent pink → #D341C4
Muted gray → #666666


---

## Development Tools

- Raspberry Pi server
- VS Code Remote SSH
- Git
- GitHub

---

# 📂 Project Structure


yogi/
│
├── app.py # Main Flask application
│
├── templates/ # Jinja2 HTML templates
│ ├── base.html
│ ├── index.html
│ ├── login.html
│ ├── register.html
│ ├── classes.html
│ ├── pricing.html
│ ├── schedule.html
│ ├── book.html
│ ├── success.html
│ ├── full.html
│ └── admin_bookings.html
│
├── static/
│ ├── css/
│ ├── js/
│ └── img/
│
└── README.md


---

# 🗄 Database Schema

## users

| column | type |
|------|------|
| id (PK) | int |
| full_name | varchar |
| email | varchar |
| phone | varchar |
| gender | varchar |
| birthday | date |
| password_hash | varchar |
| is_admin | tinyint |

`is_admin` controls administrator access.


0 → normal user
1 → admin user


---

## classes

| column | type |
|------|------|
| id (PK) | int |
| title | varchar |
| description | text |
| date | date |
| start_time | time |
| duration_minutes | int |
| max_spots | int |
| level | varchar |
| category | varchar |

---

## bookings

| column | type |
|------|------|
| id (PK) | int |
| class_id (FK) | int |
| user_id (FK) | int |
| full_name | varchar |
| email | varchar |
| phone | varchar |
| created_at | timestamp |

---

# 🔐 Authentication System

Passwords are **never stored as plain text**.

Flask uses Werkzeug security:


generate_password_hash()
check_password_hash()


Authentication is handled using **Flask sessions**.

Example:

```python
session["user_id"] = user["id"]
🛡 Admin System

Administrators are identified by:


is_admin = 1


Admin login page:


Protected routes use a decorator:

def admin_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return view(**kwargs)
    return wrapped_view

Example protected route:

@app.route("/admin/bookings")
@admin_required
def admin_bookings():
▶️ Running the Project
1. Navigate to project folder
cd ~/apps/yogi
2. Activate virtual environment
source .venv/bin/activate
3. Start Flask server
python app.py

Server runs on:

http://10.0.0.50:5000
👤 User Features
Logged-out users

View yoga classes

Browse weekly schedule

See pricing

Explore instructors

Logged-in users

Book classes

Auto-filled booking form

View upcoming classes

View booking history

🛡 Admin Features

Admin panel includes:

/admin/bookings


Admins can:

view all bookings

see user details

track class popularity

monitor studio activity

💻 Development Workflow

Using VS Code + Remote SSH

Open VS Code

Connect via Remote SSH

Open folder:


/home/nikolvoronina/apps/yogi


Edit files normally

Restart Flask server after changes

📤 Deployment to GitHub

Initialize repository:

git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your_user>/yogi-project.git
git push -u origin main
📃 License

MIT License

Free for personal, educational, or commercial use.

🌸 Author

Nikol Voronina

Designed in Figma
Built with Flask & MariaDB
Hosted on Raspberry Pi
