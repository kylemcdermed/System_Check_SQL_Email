import os
import psutil
import logging
import smtplib
import sqlite3
import time 



logger = logging.getLogger('main_logger')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

file_sql_logger = logging.FileHandler(filename='logging_db.db')
file_sql_logger.setLevel(logging.DEBUG)
file_sql_logger.setFormatter(formatter)

console_logger = logging.StreamHandler()
console_logger.setLevel(logging.WARNING)
console_logger.setFormatter(formatter)

logger.addHandler(file_sql_logger)
logger.addHandler(console_logger)


# Global DB connection with timeout
conn = sqlite3.connect('logging_db.db', timeout=10)  # Timeout of 10 seconds
cursor = conn.cursor()


# Function to create db_log table if it doesn't exist
def create_db_table():
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS db_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        cpu_usage REAL,
        mem_usage REAL,
        message TEXT
    )
    ''')
    conn.commit()

# Call the function to ensure the table is created before starting logging
create_db_table()


email = "kylemcdermed1@gmail.com"
password = "ickp xdvw lppm fxkt" # api key
checks = 0
last_email_time = time.time()


def display_system_health(cpu_usage,mem_usage,bars=50):
    
    cpu_percent = (cpu_usage / 100.0)
    cpu_bar = '█' * int(cpu_percent * bars) + '-' * (bars - int(cpu_percent * bars))
    mem_percent = (mem_usage / 100.0)
    mem_bar = '█' * int(mem_percent * bars) + '-' * (bars - int(mem_percent * bars))

    global checks

    if cpu_percent >= 85:
        checks += 1

    return cpu_percent, cpu_bar, mem_percent, mem_bar, checks


def send_email(subject, message):
    try:
        smtp_object = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_object.ehlo()
        smtp_object.starttls()
        smtp_object.login(email, password)
        msg = f"Subject: {subject}\n{message}"
        smtp_object.sendmail(email, email, msg.encode('utf-8'))
        logging.info(f"Email sent: {subject}")
    except Exception as e:
        logging.error(f"Error sending email: {e}")


# Log System update every 5 minutes
while True:
    
    cpu_usage = psutil.cpu_percent(interval=1)
    mem_usage = psutil.virtual_memory().percent

    cpu_percent, cpu_bar, mem_percent, mem_bar, checks = display_system_health(cpu_usage, mem_usage)

    if cpu_percent >= 85 and checks >= 3:
        # SEND EMAIL
        checks = 0
        logging.critical('System is experiencing a critical alert!') 
        subject = "CPU 80% OVERLOADED!"
        message = f'''Attention,\n\nYour Local Host System has a critical update.\n\nCPU Percentage of {cpu_percent}%\n{cpu_bar}\nMEM Percentage of {mem_percent}%\n{mem_bar}\n'''
        send_email(subject,message)
    else:
        logging.info('System is operating normally.')
        subject = "Local Host 5 Minute System Status"
        message = f'''\nGreetings,\n\nYour Local Host System has an update.\n\nCPU Percentage of {cpu_percent}%\n{cpu_bar}\nMEM Percentage of {mem_percent}%\n{mem_bar}\n'''
        send_email(subject,message)

    # Write to the database directly (overwrite data for simplicity)
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')  # Current time as timestamp
    with sqlite3.connect('logging_db.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO db_log (timestamp, cpu_usage, mem_usage, message)
        VALUES (?, ?, ?, ?)
        ''', (timestamp, cpu_percent, mem_percent, message))
        conn.commit()

    time.sleep(5) 

