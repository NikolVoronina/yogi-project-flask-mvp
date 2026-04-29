from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
)

import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, redirect, url_for
import datetime as dt

def format_time_range(start_td, duration_minutes):
    """
    start_td – timedelta из MySQL TIME
    duration_minutes – длительность занятия в минутах
    Возвращает время начала и конца в формате HH:MM
    """
    if start_td is None or duration_minutes is None:
        return "", ""

    total_seconds = int(start_td.total_seconds())

    start_h = (total_seconds // 3600) % 24
    start_m = (total_seconds % 3600) // 60
    start_str = f"{start_h:02d}:{start_m:02d}"

    end_total_seconds = total_seconds + int(duration_minutes) * 60
    end_h = (end_total_seconds // 3600) % 24
    end_m = (end_total_seconds % 3600) // 60
    end_str = f"{end_h:02d}:{end_m:02d}"

    return start_str, end_str

app = Flask(__name__)

# SECRET KEY для сессий

app.secret_key = "super-secret-yogi-key"


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Параметры базы данных

DB_HOST = "localhost"
DB_USER = "yogi_user"
DB_PASSWORD = "Yogi2025!"
DB_NAME = "yogi"

CLASS_CATEGORY_OPTIONS = [
    {"value": "yoga", "label": "Yoga", "color": "green"},
    {"value": "prenatal-yoga", "label": "Prenatal Yoga", "color": "pink"},
    {"value": "stretching", "label": "Stretching", "color": "blue"},
]

CLASS_LEVEL_OPTIONS = [
    {"value": "for-beginners", "label": "For beginners"},
    {"value": "intermediate", "label": "Intermediate"},
    {"value": "pro", "label": "Pro"},
]

CATEGORY_LOOKUP = {item["value"]: item for item in CLASS_CATEGORY_OPTIONS}
LEVEL_LOOKUP = {item["value"]: item for item in CLASS_LEVEL_OPTIONS}

CATEGORY_ALIASES = {
    "yoga": "yoga",
    "general": "yoga",
    "prenatal": "prenatal-yoga",
    "prental yoga": "prenatal-yoga",
    "prenatal yoga": "prenatal-yoga",
    "stretching": "stretching",
}

LEVEL_ALIASES = {
    "for beginners": "for-beginners",
    "beginner": "for-beginners",
    "beginners": "for-beginners",
    "all levels": "for-beginners",
    "intermediate": "intermediate",
    "pro": "pro",
    "advanced": "pro",
}

BOOKING_NOTE_COLUMN_READY = False


def normalize_category(value):
    key = (value or "").strip().lower()
    key = CATEGORY_ALIASES.get(key, key)
    if key in CATEGORY_LOOKUP:
        return key
    return "yoga"


def normalize_level(value):
    key = (value or "").strip().lower()
    key = LEVEL_ALIASES.get(key, key)
    if key in LEVEL_LOOKUP:
        return key
    return "for-beginners"


def enrich_class_record(cls):
    category_key = normalize_category(cls.get("category"))
    level_key = normalize_level(cls.get("level"))

    cls["category"] = category_key
    cls["level"] = level_key
    cls["category_label"] = CATEGORY_LOOKUP[category_key]["label"]
    cls["category_color"] = CATEGORY_LOOKUP[category_key]["color"]
    cls["level_label"] = LEVEL_LOOKUP[level_key]["label"]
    return cls


def ensure_booking_note_column():
    global BOOKING_NOTE_COLUMN_READY

    if BOOKING_NOTE_COLUMN_READY:
        return True

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = 'bookings'
                  AND COLUMN_NAME = 'booking_note'
                """,
                (DB_NAME,),
            )
            exists = cursor.fetchone()

            if not exists:
                cursor.execute("ALTER TABLE bookings ADD COLUMN booking_note TEXT NULL")
                conn.commit()

        BOOKING_NOTE_COLUMN_READY = True
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
    )

def get_current_user():
    """Возвращает словарь с данными юзера или None."""

    user_id = session.get("user_id")

    if not user_id:
        return None

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
    finally:
        conn.close()

    return user


def login_required(view):
    """Декоратор для страниц, требующих логин"""

    @wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(**kwargs)

    return wrapped_view


@app.route("/")
def index():
    """Главная страница"""

    current_user = get_current_user()

    today = dt.date.today()
    start_of_week = today - dt.timedelta(days=today.weekday())
    end_of_week = start_of_week + dt.timedelta(days=5)

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT
                    c.id,
                    c.title,
                    c.description,
                    c.date,
                    c.start_time,
                    c.duration_minutes,
                    c.max_spots,
                    c.level,
                    c.category,
                    COUNT(b.id) AS booked_spots
                FROM classes c
                LEFT JOIN bookings b ON b.class_id = c.id
                WHERE c.date BETWEEN %s AND %s
                GROUP BY c.id
                ORDER BY c.date, c.start_time;
            """

            cursor.execute(sql, (start_of_week, end_of_week))
            classes = cursor.fetchall()

            for cls in classes:
                start_td = cls["start_time"]
                duration = cls["duration_minutes"]

                start_str, end_str = format_time_range(start_td, duration)

                cls["start_time_str"] = start_str
                cls["end_time_str"] = end_str
                enrich_class_record(cls)

    finally:
        conn.close()

    categories = CLASS_CATEGORY_OPTIONS

    classes_by_date = {}

    for cls in classes:
        d = cls["date"]
        classes_by_date.setdefault(d, []).append(cls)

    week_days = []

    for i in range(6):
        day_date = start_of_week + dt.timedelta(days=i)

        week_days.append(
            {
                "date": day_date,
                "weekday_label": day_date.strftime("%A"),
            }
        )

    return render_template(
        "index.html",
        classes=classes,
        week_days=week_days,
        classes_by_date=classes_by_date,
        categories=categories,
        current_user=current_user,
    )

# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    current_user = get_current_user()

    if current_user:
        return redirect(url_for("index"))

    error = None

    if request.method == "POST":

        full_name = request.form.get("full_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        gender = request.form.get("gender")
        birthday = request.form.get("birthday") or None
        password = request.form.get("password")

        if not full_name or not email or not password:
            error = "Name, e-mail og passord er påkrevd."

        else:

            conn = get_db_connection()

            try:
                with conn.cursor() as cursor:

                    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                    existing = cursor.fetchone()

                    if existing:
                        error = "Bruker med denne e-posten finnes allerede."

                    else:

                        password_hash = generate_password_hash(password)

                        sql = """
                        INSERT INTO users
                        (full_name, email, phone, gender, birthday, password_hash)
                        VALUES (%s,%s,%s,%s,%s,%s)
                        """

                        cursor.execute(
                            sql,
                            (
                                full_name,
                                email,
                                phone,
                                gender,
                                birthday,
                                password_hash,
                            ),
                        )

                        conn.commit()

                        user_id = cursor.lastrowid

                        session["user_id"] = user_id

                        return redirect(url_for("index"))

            finally:
                conn.close()

    return render_template("register.html", error=error, current_user=None)


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    current_user = get_current_user()

    if current_user:
        if session.get("is_admin"):
            return redirect(url_for("admin_classes"))
        return redirect(url_for("index"))

    error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
        finally:
            conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["is_admin"] = bool(user["is_admin"])

            if user["is_admin"] == 1:
                return redirect(url_for("admin_classes"))

            return redirect(url_for("index"))

        error = "Feil e-post eller passord."

    return render_template("login.html", error=error, current_user=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))




# ---------------- STATIC PAGES ----------------

@app.route("/classes")
def classes():
    return render_template("classes.html")

@app.route("/pricing")
def pricing():
    current_user = get_current_user()

    return render_template("pricing.html", current_user=current_user)


# ---------------- BOOKING ----------------

@app.route("/book/<int:class_id>", methods=["GET", "POST"])
@login_required
def book(class_id):
    current_user = get_current_user()

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT
                    c.id,
                    c.title,
                    c.description,
                    c.date,
                    c.start_time,
                    c.duration_minutes,
                    c.max_spots,
                    COUNT(b.id) AS booked_spots
                FROM classes c
                LEFT JOIN bookings b ON b.class_id = c.id
                WHERE c.id = %s
                GROUP BY c.id;
                """,
                (class_id,),
            )

            yoga_class = cursor.fetchone()

            if not yoga_class:
                return redirect(url_for("index"))

            if request.method == "POST":

                full_name = current_user["full_name"]
                email = current_user["email"]
                phone = current_user.get("phone")
                booking_note = request.form.get("booking_note", "").strip()

                if yoga_class["booked_spots"] >= yoga_class["max_spots"]:

                    return render_template(
                        "full.html",
                        yoga_class=yoga_class,
                        current_user=current_user,
                    )

                if ensure_booking_note_column():
                    insert_sql = """
                    INSERT INTO bookings
                    (class_id, user_id, full_name, email, phone, booking_note)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(
                        insert_sql,
                        (class_id, current_user["id"], full_name, email, phone, booking_note or None),
                    )
                else:
                    insert_sql = """
                    INSERT INTO bookings
                    (class_id, user_id, full_name, email, phone)
                    VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(
                        insert_sql,
                        (class_id, current_user["id"], full_name, email, phone),
                    )

                conn.commit()

                return render_template(
                    "success.html",
                    yoga_class=yoga_class,
                    current_user=current_user,
                )

    finally:
        conn.close()

    return render_template("book.html", yoga_class=yoga_class, current_user=current_user)


# ---------------- MY CLASSES ----------------

@app.route("/my-classes")
@login_required
def my_classes():
    current_user = get_current_user()

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            sql_future = """
            SELECT b.*, c.title AS class_title, c.date, c.start_time
            FROM bookings b
            JOIN classes c ON c.id = b.class_id
            WHERE b.user_id = %s AND c.date >= CURDATE()
            ORDER BY c.date, c.start_time
            """

            cursor.execute(sql_future, (current_user["id"],))
            future_classes = cursor.fetchall()

            sql_past = """
            SELECT b.*, c.title AS class_title, c.date, c.start_time
            FROM bookings b
            JOIN classes c ON c.id = b.class_id
            WHERE b.user_id = %s AND c.date < CURDATE()
            ORDER BY c.date DESC, c.start_time DESC
            """

            cursor.execute(sql_past, (current_user["id"],))
            past_classes = cursor.fetchall()

    finally:
        conn.close()

    return render_template(
        "my_membership.html",
        current_user=current_user,
        future_classes=future_classes,
        past_classes=past_classes,
    )


# ---------------- ADMIN BOOKINGS ----------------
@app.route("/admin/bookings")
@admin_required
def admin_bookings():
    current_user = get_current_user()
    has_booking_note = ensure_booking_note_column()

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            note_column = "b.booking_note" if has_booking_note else "NULL AS booking_note"

            sql = f"""
            SELECT
                b.id,
                b.full_name,
                b.email,
                b.phone,
                {note_column},
                b.created_at,
                c.title AS class_title,
                c.date AS class_date,
                c.start_time AS class_time
            FROM bookings b
            JOIN classes c ON c.id = b.class_id
            ORDER BY b.created_at DESC
            """

            cursor.execute(sql)

            bookings = cursor.fetchall()

    finally:
        conn.close()

    return render_template(
        "admin/bookings.html",
        bookings=bookings,
        current_user=current_user,
    )


# ---------------- SCHEDULE ----------------

@app.route("/schedule")
def schedule():
    current_user = get_current_user()

    today = dt.date.today()

    start_of_week = today - dt.timedelta(days=today.weekday())
    end_of_week = start_of_week + dt.timedelta(days=5)

    requested_category = request.args.get("category", "all")
    current_category = "all" if requested_category == "all" else normalize_category(requested_category)

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            sql = """
            SELECT
                c.id,
                c.title,
                c.description,
                c.date,
                c.start_time,
                c.duration_minutes,
                c.max_spots,
                c.level,
                c.category,
                COUNT(b.id) AS booked_spots
            FROM classes c
            LEFT JOIN bookings b ON b.class_id = c.id
            WHERE c.date BETWEEN %s AND %s
            GROUP BY c.id
            ORDER BY c.date, c.start_time
            """

            cursor.execute(sql, (start_of_week, end_of_week))

            classes = cursor.fetchall()

            for cls in classes:

                start_td = cls["start_time"]
                duration = cls["duration_minutes"]

                start_str, end_str = format_time_range(start_td, duration)

                cls["start_time_str"] = start_str
                cls["end_time_str"] = end_str
                enrich_class_record(cls)

    finally:
        conn.close()

    categories = CLASS_CATEGORY_OPTIONS

    if current_category != "all":
        filtered_classes = [c for c in classes if c["category"] == current_category]
    else:
        filtered_classes = classes

    classes_by_date = {}

    for cls in filtered_classes:
        d = cls["date"]
        classes_by_date.setdefault(d, []).append(cls)

    week_days = []

    for i in range(6):
        day_date = start_of_week + dt.timedelta(days=i)

        week_days.append(
            {
                "date": day_date,
                "weekday_label": day_date.strftime("%A"),
            }
        )

    return render_template(
        "schedule.html",
        current_user=current_user,
        week_days=week_days,
        classes_by_date=classes_by_date,
        categories=categories,
        current_category=current_category,
    )


def get_admin_classes_data():
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    classes.*,
                    COUNT(bookings.id) AS booking_count
                FROM classes
                LEFT JOIN bookings ON classes.id = bookings.class_id
                GROUP BY classes.id
                ORDER BY classes.date ASC, classes.start_time ASC
            """)
            classes = cursor.fetchall()
            for yoga_class in classes:
                enrich_class_record(yoga_class)
            return classes
    finally:
        conn.close()


# ---------------- ADMIN CREATE CLASS ----------------

@app.route("/admin/create_classes")
@admin_required
def admin_create_class():
    return redirect(url_for("admin_classes"))



@app.route("/admin/classes", methods=["GET", "POST"])
@admin_required
def admin_classes():
    current_user = get_current_user()
    error = None
    success = None
    form_data = {
        "title": "",
        "description": "",
        "date": "",
        "start_time": "",
        "duration_minutes": "",
        "max_spots": "",
        "level": CLASS_LEVEL_OPTIONS[0]["value"],
        "category": CLASS_CATEGORY_OPTIONS[0]["value"],
    }

    if request.method == "POST":
        for key in form_data:
            form_data[key] = request.form.get(key, "").strip()

        if not form_data["title"] or not form_data["date"] or not form_data["start_time"] or not form_data["duration_minutes"] or not form_data["max_spots"]:
            error = "Please fill in all required fields."
        elif normalize_category(form_data["category"]) not in CATEGORY_LOOKUP or normalize_level(form_data["level"]) not in LEVEL_LOOKUP:
            error = "Please select valid category and level from the list."
        else:
            normalized_category = normalize_category(form_data["category"])
            normalized_level = normalize_level(form_data["level"])

            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO classes
                        (title, description, date, start_time, duration_minutes, max_spots, level, category)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        form_data["title"],
                        form_data["description"],
                        form_data["date"],
                        form_data["start_time"],
                        int(form_data["duration_minutes"]),
                        int(form_data["max_spots"]),
                        normalized_level,
                        normalized_category,
                    ))
                    conn.commit()

                success = "Class created successfully."
                form_data = {
                    "title": "",
                    "description": "",
                    "date": "",
                    "start_time": "",
                    "duration_minutes": "",
                    "max_spots": "",
                    "level": CLASS_LEVEL_OPTIONS[0]["value"],
                    "category": CLASS_CATEGORY_OPTIONS[0]["value"],
                }

            except Exception as e:
                error = f"Database error: {e}"

            finally:
                conn.close()

    classes = get_admin_classes_data()

    return render_template(
        "admin/classes.html",
        classes=classes,
        current_user=current_user,
        error=error,
        success=success,
        form_data=form_data,
        category_options=CLASS_CATEGORY_OPTIONS,
        level_options=CLASS_LEVEL_OPTIONS,
    )


@app.route("/admin/class/<int:class_id>/delete", methods=["POST"])
@admin_required
def admin_delete_class(class_id):
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM bookings WHERE class_id = %s", (class_id,))
            cursor.execute("DELETE FROM classes WHERE id = %s", (class_id,))
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        conn.close()

    return redirect(url_for("admin_classes"))



@app.route("/admin/class/<int:class_id>/bookings")
@admin_required
def admin_class_bookings(class_id):
    current_user = get_current_user()
    has_booking_note = ensure_booking_note_column()
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM classes
                WHERE id = %s
            """, (class_id,))
            yoga_class = cursor.fetchone()

            note_column = "bookings.booking_note" if has_booking_note else "NULL AS booking_note"

            cursor.execute(f"""
                SELECT 
                    users.full_name,
                    users.email,
                    users.phone,
                    {note_column},
                    bookings.created_at
                FROM bookings
                JOIN users ON bookings.user_id = users.id
                WHERE bookings.class_id = %s
                ORDER BY bookings.created_at DESC
            """, (class_id,))
            bookings = cursor.fetchall()

    finally:
        conn.close()

    return render_template(
        "admin/class_bookings.html",
        yoga_class=yoga_class,
        bookings=bookings,
        current_user=current_user,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)