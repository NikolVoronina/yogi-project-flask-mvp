# YOGI – Yoga Studio Web App

## Overview

YOGI is a full-featured web application for managing a yoga studio.  
Users can browse classes, book sessions, and request private lessons.  
Admins get a dedicated panel to manage classes, view bookings, and handle individual lesson requests.

This project was developed as part of my IT studies.

---

## Features

### User
- Register and log in securely
- Browse available yoga classes
- Book classes with an optional note
- View personal booking history
- Request a private (individual) lesson — choose a preferred date and instructor
- View pricing plans

### Admin
- Log in via the same login page — automatically redirected to admin panel
- Role-based navigation (admin sees different menu than regular users)
- Create and manage classes (title, description, date, time, duration, instructor, spots)
- View all bookings across all classes
- View per-class booking lists
- Manage private lesson requests — see status, mark as completed or pending
- Dashboard with pending private request counter

---

## Tech Stack

- **Python** (Flask)
- **MariaDB / MySQL** (via PyMySQL)
- **HTML, CSS** (custom design system, no external UI framework)
- **Jinja2** (templating)
- **Werkzeug** (password hashing)
- **python-dotenv** (environment config)

---

## Project Structure

```
yogi/
│
├── app.py                  # All routes, auth, DB logic, migrations
├── wsgi.py                 # WSGI entry point
├── requirements.txt
│
├── templates/
│   ├── base.html           # Shared layout, role-based navigation
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── classes.html
│   ├── schedule.html
│   ├── pricing.html
│   ├── book.html
│   ├── my_membership.html
│   ├── private_request.html
│   └── admin/
│       ├── classes.html
│       ├── create_classes.html
│       ├── bookings.html
│       ├── class_bookings.html
│       └── admin_private_requests.html
│
├── static/
│   └── img/
│
└── README.md
```

---

## How It Works

- Flask handles all routing and session management
- Passwords are hashed with Werkzeug before storing in the database
- `is_admin` flag in the user table controls access to admin routes
- Decorators `@login_required` and `@admin_required` protect routes
- Database schema evolves at runtime — new columns are added automatically on first request if missing
- Private lesson requests are stored with a `status` field (`pending` / `completed`) and can be toggled by admins

---

## Design System

- Custom CSS with CSS variables (`--yogi-green`, `--yogi-dark`, `--yogi-pink`, `--yogi-muted`)
- Poppins font family
- Consistent component patterns: pill badges, rounded cards, dark admin tables
- No external UI frameworks (Bootstrap, Tailwind, etc.)

---

## What I Learned

- Flask routing, blueprints, and application structure
- SQL and relational database integration
- Secure user authentication and session handling
- Role-based access control with decorators
- Form handling and server-side validation
- Iterative feature development and UI/UX design
- Runtime database migration patterns  