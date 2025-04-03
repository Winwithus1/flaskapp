import sqlite3
import random
import smtplib
import time
from email.mime.text import MIMEText
from datetime import datetime
import threading
from flask import Flask, render_template, request, redirect, url_for

# Flask app setup
app = Flask("WinWithUs")

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "gurs8919@gmail.com"
EMAIL_PASSWORD = "ymse hezw dszr umsc"  # Use App Password from Google

def init_db():
    conn = sqlite3.connect("winwithus.db")
    c = conn.cursor()

    # ❌ REMOVE this line to keep existing data
    # c.execute("DROP TABLE IF EXISTS users")

    # ✅ Create users table only if it does not exist
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT NOT NULL,
                 email TEXT UNIQUE NOT NULL,
                 balance REAL DEFAULT 0,
                 otp TEXT,
                 last_participation TIMESTAMP)""")

    # ✅ Create lottery tickets table only if it does not exist
    c.execute("""CREATE TABLE IF NOT EXISTS lottery_tickets (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 ticket_number TEXT UNIQUE NOT NULL,
                 purchase_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY (user_id) REFERENCES users(id))""")

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

init_db()  # Ensure DB is created on startup

# Function to send emails
def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        print(f"📩 Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")

# Function to register a new user
def register_user(name, email):
    conn = sqlite3.connect("winwithus.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (name, email) VALUES (?, ?)", (name, email))
        conn.commit()
        print("✅ User registered successfully!")
    except sqlite3.IntegrityError:
        print("⚠️ User already exists!")
    finally:
        conn.close()

# Add money to user balance
def add_money(email, amount):
    conn = sqlite3.connect("winwithus.db")
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE email = ?", (amount, email))
    conn.commit()
    conn.close()
    print(f"💰 {amount} added to {email}'s balance.")

# Buy lottery ticket
def buy_ticket(email):
    conn = sqlite3.connect("winwithus.db")
    c = conn.cursor()
    c.execute("SELECT id, balance FROM users WHERE email = ?", (email,))
    user = c.fetchone()

    if user and user[1] >= 10:  # Ticket price is 10
        ticket_number = str(random.randint(100000, 999999))
        c.execute("INSERT INTO lottery_tickets (user_id, ticket_number) VALUES (?, ?)", (user[0], ticket_number))
        c.execute("UPDATE users SET balance = balance - 10 WHERE id = ?", (user[0],))
        conn.commit()
        conn.close()
        print(f"🎟️ Ticket {ticket_number} purchased for {email}.")
        return ticket_number
    else:
        conn.close()
        print("❌ Insufficient balance or user not found.")

# Function to send OTP
def send_otp(email):
    otp = str(random.randint(100000, 999999))
    conn = sqlite3.connect("winwithus.db")
    c = conn.cursor()
    c.execute("UPDATE users SET otp = ? WHERE email = ?", (otp, email))
    conn.commit()
    conn.close()
    send_email(email, "WinWithUs: Your OTP for Login", f"Your OTP is: {otp}")

# Function to verify OTP
def verify_otp(email, otp):
    conn = sqlite3.connect("winwithus.db")
    c = conn.cursor()
    c.execute("SELECT otp FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    
    if row and row[0] == otp:
        c.execute("UPDATE users SET otp = NULL WHERE email = ?", (email,))
        conn.commit()
        print("✅ Login successful!")
    else:
        print("❌ Invalid OTP!")

    conn.close()

# Function to confirm participation
def confirm_participation(email):
    conn = sqlite3.connect("winwithus.db")
    c = conn.cursor()
    c.execute("UPDATE users SET last_participation = CURRENT_TIMESTAMP WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    print("✅ Participation confirmed!")

# Function to send weekly reminders
def send_reminders():
    while True:
        conn = sqlite3.connect("winwithus.db")
        c = conn.cursor()
        c.execute("SELECT email FROM users WHERE last_participation IS NULL OR last_participation < date('now', '-7 days')")
        users = c.fetchall()
        conn.close()

        if users:
            for user in users:
                send_email(user[0], "WinWithUs Reminder", "Click here to confirm your participation.")
            print("🔔 Weekly reminders sent!")
        else:
            print("No users to send reminders to.")

        time.sleep(604800)  # Wait 7 days (1 week)

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    register_user(name, email)
    return redirect(url_for('index'))

@app.route('/send_otp', methods=['POST'])
def send_otp_route():
    email = request.form['email']
    send_otp(email)
    return redirect(url_for('index'))

@app.route('/verify_otp', methods=['POST'])
def verify_otp_route():
    email = request.form['email']
    otp = request.form['otp']
    verify_otp(email, otp)
    return redirect(url_for('index'))

@app.route('/confirm_participation', methods=['POST'])
def confirm_participation_route():
    email = request.form['email']
    confirm_participation(email)
    return redirect(url_for('index'))

# Start weekly reminder thread
threading.Thread(target=send_reminders, daemon=True).start()

# Start Flask app
if __name__ == "__main__":
    app.run(debug=True)
