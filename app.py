from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "niwas_secret_key_2024"

def get_db():
    conn = sqlite3.connect("niwas.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT,
        amenities TEXT,
        image_url TEXT,
        available INTEGER DEFAULT 1
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        room_id INTEGER,
        guest_name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        check_in TEXT NOT NULL,
        check_out TEXT NOT NULL,
        guests INTEGER NOT NULL,
        total_price REAL NOT NULL,
        status TEXT DEFAULT 'confirmed',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.execute('''INSERT OR IGNORE INTO users (name, email, password) 
                    VALUES ('Admin', 'admin@niwas.com', 'admin123')''')
    rooms_data = [
        ('Deluxe Room', 'Deluxe', 4999, 'Spacious room with city view and modern amenities', 
         'WiFi,AC,TV,Mini Bar,Room Service', 
         'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=800', 1),
        ('Premium Suite', 'Suite', 9999, 'Luxurious suite with panoramic views and premium furnishings',
         'WiFi,AC,TV,Mini Bar,Jacuzzi,Butler Service',
         'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800', 1),
        ('Royal Suite', 'Royal', 19999, 'The pinnacle of luxury with exclusive royal treatment',
         'WiFi,AC,TV,Mini Bar,Private Pool,Butler,Spa Access',
         'https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=800', 1),
        ('Classic Room', 'Classic', 2999, 'Comfortable and cozy room perfect for business travelers',
         'WiFi,AC,TV,Room Service',
         'https://images.unsplash.com/photo-1505693314120-0d443867891c?w=800', 1),
        ('Garden Villa', 'Villa', 14999, 'Private villa with lush garden and personal pool',
         'WiFi,AC,TV,Private Pool,Garden,BBQ,Butler',
         'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800', 1),
        ('Ocean View Room', 'Deluxe', 6999, 'Stunning ocean views with premium beach access',
         'WiFi,AC,TV,Beach Access,Mini Bar',
         'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=800', 1),
    ]
    for room in rooms_data:
        conn.execute('''INSERT OR IGNORE INTO rooms (name, type, price, description, amenities, image_url, available)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''', room)
    conn.commit()
    conn.close()

@app.route("/")
def index():
    conn = get_db()
    rooms = conn.execute("SELECT * FROM rooms WHERE available = 1 LIMIT 3").fetchall()
    conn.close()
    return render_template("index.html", rooms=rooms)

@app.route("/rooms")
def rooms():
    filter_type = request.args.get("type", "All")
    conn = get_db()
    if filter_type == "All":
        rooms = conn.execute("SELECT * FROM rooms WHERE available = 1").fetchall()
    else:
        rooms = conn.execute("SELECT * FROM rooms WHERE available = 1 AND type = ?", (filter_type,)).fetchall()
    conn.close()
    return render_template("rooms.html", rooms=rooms, filter_type=filter_type)

@app.route("/book/<int:room_id>", methods=["GET", "POST"])
def book(room_id):
    conn = get_db()
    room = conn.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
    if request.method == "POST":
        guest_name = request.form["guest_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        check_in = request.form["check_in"]
        check_out = request.form["check_out"]
        guests = request.form["guests"]
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
        nights = (check_out_date - check_in_date).days
        total_price = nights * room["price"]
        user_id = session.get("user_id", None)
        conn.execute('''INSERT INTO bookings (user_id, room_id, guest_name, email, phone, check_in, check_out, guests, total_price)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (user_id, room_id, guest_name, email, phone, check_in, check_out, guests, total_price))
        conn.commit()
        conn.close()
        return redirect(url_for("booking_success"))
    conn.close()
    return render_template("booking.html", room=room)

@app.route("/booking-success")
def booking_success():
    return render_template("booking_success.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password)).fetchone()
        conn.close()
        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["is_admin"] = (email == "admin@niwas.com")
            return redirect(url_for("index"))
        return render_template("login.html", error="Invalid email or password")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except:
            conn.close()
            return render_template("register.html", error="Email already exists")
    return render_template("register.html")

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    bookings = conn.execute('''SELECT b.*, r.name as room_name FROM bookings b 
                               JOIN rooms r ON b.room_id = r.id 
                               WHERE b.user_id = ?''', (session["user_id"],)).fetchall()
    conn.close()
    return render_template("profile.html", user=user, bookings=bookings)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/admin")
def admin():
    if not session.get("is_admin"):
        return redirect(url_for("login"))
    conn = get_db()
    bookings = conn.execute('''SELECT b.*, r.name as room_name FROM bookings b 
                               JOIN rooms r ON b.room_id = r.id 
                               ORDER BY b.created_at DESC''').fetchall()
    rooms = conn.execute("SELECT * FROM rooms").fetchall()
    conn.close()
    return render_template("admin.html", bookings=bookings, rooms=rooms)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)