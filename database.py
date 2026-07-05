import os
import mysql.connector

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def connect_db():
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT")),
        ssl_ca=os.path.join(BASE_DIR, "ca.pem")
    )
    return db