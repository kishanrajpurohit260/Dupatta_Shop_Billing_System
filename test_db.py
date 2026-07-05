import mysql.connector

print("Before")

try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="dupatta_shop",
        port=3306,
        connection_timeout=5
    )

    print("Database Connected")

except Exception as e:
    print("Error:")
    print(e)

input("Enter press karo")
