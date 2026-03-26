# YOGI – Yoga Studio Web App

## Overview

YOGI is a simple web application for managing a yoga studio.  
It allows users to view and book classes, while admins can create classes directly from the website.

This project was developed as part of my IT studies.

---

## Features

### User
- Register and log in  
- View available classes  
- Book classes  

### Admin
- Log in through the same login page  
- Automatically redirected to admin panel  
- Create new classes via web interface  

---

## Tech Stack

- Python (Flask)
- MariaDB / MySQL
- HTML, CSS
- Jinja2

---

## Project Structure

```
yogi/
│
├── app.py
├── templates/
│   ├── login.html
│   ├── index.html
│   └── admin/
│       └── create_classes.html
│
├── static/
│   └── style.css
│
└── README.md
```

---

## How It Works

- The application is built with Flask  
- Data is stored in a MariaDB database  
- Passwords are hashed for security  
- The system checks if a user is admin (`is_admin`)  
- Admin users are redirected to the admin page  

---

## What I Focused On

- Connecting frontend and backend  
- Working with a real database  
- Handling login and sessions  
- Building a simple admin system  
- Keeping the interface clean and usable  

---

## What I Learned

- Flask routing and structure  
- SQL and database integration  
- User authentication  
- Form handling  
- Basic UI/UX design  

---

## Future Improvements

- Edit and delete classes  
- Display number of bookings  
- Add calendar view  
- Improve design  
- Strengthen admin security  