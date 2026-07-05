import mysql.connector

def connect_db():

    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="dupatta_shop",
        port=3306
    )

    return db