import os
import mysql.connector

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def connect_db():

    if os.getenv("DB_HOST"):   # Render/Aiven
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT")),
            ssl_ca=os.path.join(BASE_DIR, "ca.pem")
        )

    else:   # Local XAMPP
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="dupatta_shop",
            port=3306
        )