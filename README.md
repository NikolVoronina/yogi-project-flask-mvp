# 🌿 YOGI — Yoga Studio Web App  
**Modern booking system for yoga studios, designed with a clean Scandinavian aesthetic and implemented using Flask, MariaDB, and Raspberry Pi.**

---

## 🚀 Overview

YOGI is a full-stack application designed for small and mid-sized yoga studios.  
It includes:

- User authentication (register/login/logout)
- Class scheduling system
- Booking functionality with limited spots
- Weekly calendar (auto-generated)
- Personal dashboard for users
- Admin booking overview
- Fully responsive UI based on custom Figma designs

The project is optimized to run even on a **Raspberry Pi** as a lightweight server.

---

## 🛠️ Tech Stack

### **Backend**
- Python 3  
- Flask (Jinja2 templates)  
- PyMySQL  
- Werkzeug security (password hashing)

### **Database**
- MariaDB / MySQL  
- Hosted on Raspberry Pi

### **Frontend**
- HTML5  
- CSS3  
- Figma → Production templates  
- Custom design system  
  - `#BAD341` (primary green)  
  - `#1E1E1E` (dark)  
  - `#D341C4` (pink)  
  - `#666666` (muted)

### **Deployment / Dev Tools**
- Raspberry Pi Server  
- VS Code Remote SSH  
- Git + GitHub  

---



yogi/
│
├── app.py # Main Flask application
├── templates/ # HTML (Jinja2) templates
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
│ ├── img/ # Studio photos, instructors, etc.
│ ├── css/
│ └── js/
│
└── README.md


---

## 🗄️ Database Schema

### **users**
| column          | type      |
|-----------------|-----------|
| id (PK)         | int       |
| full_name       | varchar   |
| email           | varchar   |
| phone           | varchar   |
| gender          | varchar   |
| birthday        | date      |
| password_hash   | varchar   |

### **classes**
| column          | type      |
|-----------------|-----------|
| id (PK)         | int       |
| title           | varchar   |
| description     | text      |
| date            | date      |
| start_time      | time      |
| duration_minutes| int       |
| max_spots       | int       |

### **bookings**
| column          | type      |
|-----------------|-----------|
| id (PK)         | int       |
| class_id (FK)   | int       |
| user_id (FK)    | int       |
| full_name       | varchar   |
| email           | varchar   |
| phone           | varchar   |
| created_at      | timestamp |

---

## ▶️ Running the Project (Local or Raspberry Pi)

### 1. Navigate to project folder

```bash
cd ~/apps/yogi

2. Activate virtual environment
source .venv/bin/activate

3. Run the app
python app.py


Backend runs on:

http://10.0.0.50:5000

🔐 User Features
Logged-out

Browse classes

View schedule

Read instructors

View pricing

Logged-in

Book available classes

Auto-filled booking data

View upcoming classes

View past classes

🛡 Admin Features

Minimal admin dashboard:

View all bookings

See all user/class info

Ordered by newest bookings

💻 Development Workflow (VS Code + SSH)

Open VS Code

Use Remote SSH to connect to Raspberry Pi

Open folder /home/nikolvoronina/apps/yogi

Edit files normally

Restart server after changes

📤 Deployment to GitHub
Initialize repository (on Raspberry Pi)
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your_user>/yogi-project.git
git push -u origin main

📃 License

MIT License — use it freely for personal, educational, or commercial projects.

🌸 Author

Created with love and aesthetics by Nikol Voronina
Designed in Figma · Built on Raspberry Pi

## 📦 Project Structure

