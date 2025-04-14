import os
import sqlite3
import random
import smtplib
import time
from email.mime.text import MIMEText
from datetime import datetime
import threading
from flask import Flask, render_template, request, redirect, url_for, session

# Flask app setup
app = Flask("WinWithUs")
app.secret_key = os.urandom(24)  # Required for session handling

# Email Configuration (use environment variables for security)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "gurs8919@gmail.com"
EMAIL_PASSWORD = "ymse hezw dszr umsc"  # Use App Password from Google

# Initialize the database
def init_db():
    conn = sqlite3.connect("winwithus.db")
    c = conn.cursor()

    # Create users table
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        balance REAL DEFAULT 0,
        otp TEXT,
        last_participation TIMESTAMP,
        reminder_frequency TEXT DEFAULT 'weekly')""")

    # Create lottery tickets table
    c.execute("""CREATE TABLE IF NOT EXISTS lottery_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        ticket_number TEXT UNIQUE NOT NULL,
        purchase_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id))""")

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

init_db()

# Function to send email
def send_email(to_email, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        print(f"📩 Email sent to {to_email}")
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed. Check your App Password or Gmail security settings.")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")

# Threaded function for sending reminders
stop_reminders = threading.Event()

def send_reminders():
    while not stop_reminders.is_set():
        try:
            print("⏰ Checking for users to remind...")
            conn = sqlite3.connect("winwithus.db", check_same_thread=False)
            c = conn.cursor()
            c.execute("SELECT email, reminder_frequency FROM users WHERE last_participation IS NULL OR last_participation < date('now', '-7 days')")
            users = c.fetchall()
            conn.close()

            if users:
                for email, frequency in users:
                    if frequency == 'weekly':
                        send_email(email, "WinWithUs Reminder", "Don't forget to participate this week!")
                    elif frequency == 'biweekly':
                        send_email(email, "WinWithUs Reminder", "Don't forget to participate this bi-weekly period!")
                    else:
                        send_email(email, "WinWithUs Reminder", "Don't forget to participate soon!")

                print("🔔 Weekly reminders sent.")
            else:
                print("📭 No users need reminders.")
        except Exception as e:
            print(f"⚠️ Reminder thread error: {e}")

        stop_reminders.wait(604800)  # Wait for 1 week

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registration1')
def registration1():
    return render_template('registration1.html')

@app.route('/submit_registration', methods=['POST'])
def submit_registration():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if password != confirm_password:
        return "❌ Passwords do not match."

    session['user'] = {
        'name': name,
        'email': email,
        'balance': 50  # Default balance or logic to fetch from DB
    }

    return redirect(url_for('manual'))

@app.route('/manual')
def manual():
    return render_template('manual.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('registration1'))

    user = session['user']
    return render_template('dashboard.html', name=user['name'], email=user['email'], balance=user['balance'])

@app.route('/legal_lottery')
def legal_lottery():
    return render_template('legal_lottery.html')

@app.route('/reminders', methods=['GET', 'POST'])
def reminders():
    print("Reminder sent!")
    return redirect(url_for('dashboard'))

# Start the app
if __name__ == '__main__':
    reminder_thread = threading.Thread(target=send_reminders, daemon=True)
    reminder_thread.start()
    try:
        app.run(debug=True)
    finally:
        stop_reminders.set()
        reminder_thread.join()
