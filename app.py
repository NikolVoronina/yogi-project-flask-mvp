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

import datetime as dt

def format_time_range(start_td, duration_minutes):
    """start_td – timedelta из MySQL TIME, duration_minutes – int (длительность занятия в минутах). 
       Возвращает (start_str, end_str) в формате 'HH:MM'."""
    if start_td is None or duration_minutes is None:
        return "", ""

    # total_seconds для времени начала
    total_seconds = int(start_td.total_seconds())

    start_h = (total_seconds // 3600) % 24
    start_m = (total_seconds % 3600) // 60
    start_str = f"{start_h:02d}:{start_m:02d}"

    # считаем конец
    end_total_seconds = total_seconds + int(duration_minutes) * 60
    end_h = (end_total_seconds // 3600) % 24
    end_m = (end_total_seconds % 3600) // 60
    end_str = f"{end_h:02d}:{end_m:02d}"

    return start_str, end_str



app = Flask(__name__)

# СЕКРЕТНЫЙ КЛЮЧ ДЛЯ СЕССИЙ (можешь поменять на свой)
app.secret_key = "super-secret-yogi-key"

# НАСТРОЙКИ ПОДКЛЮЧЕНИЯ К БАЗЕ
DB_HOST = "localhost"
DB_USER = "yogi_user"
DB_PASSWORD = "Yogi2025!"   # <<< ТВОЙ ПАРОЛЬ
DB_NAME = "yogi"


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
    """Декоратор: требует логина для доступа к странице."""
    @wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            # можно добавить next=url_for(...)
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped_view


@app.route("/")
def index():
    """Главная: список занятий + превью расписания недели."""
    current_user = get_current_user()

    today = dt.date.today()
    start_of_week = today - dt.timedelta(days=today.weekday())   # понедельник
    end_of_week = start_of_week + dt.timedelta(days=5)           # понедельник–суббота

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
                    COUNT(b.id) AS booked_spots
                FROM classes c
                LEFT JOIN bookings b ON b.class_id = c.id
                WHERE c.date BETWEEN %s AND %s
                GROUP BY c.id
                ORDER BY c.date, c.start_time;
            """
            cursor.execute(sql, (start_of_week, end_of_week))
            classes = cursor.fetchall()

            # считаем строковые времена для каждого занятия
            for cls in classes:
                start_td = cls["start_time"]           # timedelta из TIME
                duration = cls["duration_minutes"]
                start_str, end_str = format_time_range(start_td, duration)
                cls["start_time_str"] = start_str
                cls["end_time_str"] = end_str
    finally:
        conn.close()


    # группируем по дате для сетки
    classes_by_date = {}
    for cls in classes:
        d = cls["date"]
        classes_by_date.setdefault(d, []).append(cls)

    week_days = []
    for i in range(6):  # пн–сб
        day_date = start_of_week + dt.timedelta(days=i)
        week_days.append({
            "date": day_date,
            "weekday_label": day_date.strftime("%A"),  # Monday, Tuesday...
        })

    return render_template(
        "index.html",
        classes=classes,
        week_days=week_days,
        classes_by_date=classes_by_date,
        current_user=current_user,
    )






# ---------- РЕГИСТРАЦИЯ / ЛОГИН / ЛОГАУТ ----------

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
                    # проверяем, есть ли уже пользователь с таким email
                    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                    existing = cursor.fetchone()
                    if existing:
                        error = "Bruker med denne e-posten finnes allerede."
                    else:
                        password_hash = generate_password_hash(password)
                        sql = """
                            INSERT INTO users (full_name, email, phone, gender, birthday, password_hash)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(
                            sql,
                            (full_name, email, phone, gender, birthday, password_hash),
                        )
                        conn.commit()
                        user_id = cursor.lastrowid
                        session["user_id"] = user_id
                        return redirect(url_for("index"))
            finally:
                conn.close()

    return render_template("register.html", error=error, current_user=None)


@app.route("/login", methods=["GET", "POST"])
def login():
    current_user = get_current_user()
    if current_user:
        return redirect(url_for("index"))

    error = None

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
        finally:
            conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("index"))
        else:
            error = "Feil e-post eller passord."

    return render_template("login.html", error=error, current_user=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/classes")
def classes():
    return render_template("classes.html")

@app.route("/pricing")
def pricing():
    current_user = get_current_user()
    return render_template("pricing.html", current_user=current_user)




# ---------- БРОНИРОВАНИЕ ----------

@app.route("/book/<int:class_id>", methods=["GET", "POST"])
@login_required
def book(class_id):
    """Бронирование: данные берём из профиля пользователя."""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("login"))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # получаем занятие + сколько мест занято
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
                # данные берём из профиля
                full_name = current_user["full_name"]
                email = current_user["email"]
                phone = current_user.get("phone")

                if yoga_class["booked_spots"] >= yoga_class["max_spots"]:
                    return render_template(
                        "full.html",
                        yoga_class=yoga_class,
                        current_user=current_user,
                    )

                insert_sql = """
                    INSERT INTO bookings (class_id, user_id, full_name, email, phone)
                    VALUES (%s, %s, %s, %s, %s);
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


# ---------- МОИ ЗАНЯТИЯ / АДМИН ----------

@app.route("/my-classes")
@login_required
def my_classes():
    """Страница из дизайна 'My membership' -> future + history."""
    current_user = get_current_user()

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql_future = """
                SELECT b.*, c.title AS class_title, c.date, c.start_time
                FROM bookings b
                JOIN classes c ON c.id = b.class_id
                WHERE b.user_id = %s AND c.date >= CURDATE()
                ORDER BY c.date, c.start_time;
            """
            cursor.execute(sql_future, (current_user["id"],))
            future_classes = cursor.fetchall()

            sql_past = """
                SELECT b.*, c.title AS class_title, c.date, c.start_time
                FROM bookings b
                JOIN classes c ON c.id = b.class_id
                WHERE b.user_id = %s AND c.date < CURDATE()
                ORDER BY c.date DESC, c.start_time DESC;
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


@app.route("/admin/bookings")
def admin_bookings():
    """Простая админ-страница со всеми бронированиями."""
    current_user = get_current_user()

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    b.id,
                    b.full_name,
                    b.email,
                    b.phone,
                    b.created_at,
                    c.title AS class_title,
                    c.date AS class_date,
                    c.start_time AS class_time
                FROM bookings b
                JOIN classes c ON c.id = b.class_id
                ORDER BY b.created_at DESC;
            """
            cursor.execute(sql)
            bookings = cursor.fetchall()
    finally:
        conn.close()

    return render_template(
        "admin_bookings.html",
        bookings=bookings,
        current_user=current_user,
    )



@app.route("/schedule")
def schedule():
    """Полная страница расписания той же недели."""
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
                    COUNT(b.id) AS booked_spots
                FROM classes c
                LEFT JOIN bookings b ON b.class_id = c.id
                WHERE c.date BETWEEN %s AND %s
                GROUP BY c.id
                ORDER BY c.date, c.start_time;
            """
            cursor.execute(sql, (start_of_week, end_of_week))
            classes = cursor.fetchall()

            # считаем строковые времена для каждого занятия
            for cls in classes:
                start_td = cls["start_time"]
                duration = cls["duration_minutes"]
                start_str, end_str = format_time_range(start_td, duration)
                cls["start_time_str"] = start_str
                cls["end_time_str"] = end_str
    finally:
        conn.close()

    classes_by_date = {}
    for cls in classes:
        d = cls["date"]
        classes_by_date.setdefault(d, []).append(cls)

    week_days = []
    for i in range(6):
        day_date = start_of_week + dt.timedelta(days=i)
        week_days.append({
            "date": day_date,
            "weekday_label": day_date.strftime("%A"),
        })

    return render_template(
        "schedule.html",
        current_user=current_user,
        week_days=week_days,
        classes_by_date=classes_by_date,
    )




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


