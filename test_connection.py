import mysql.connector

try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345",  # replace with your actual password
        database="qbank_app"
    )
    print("Connected successfully!")
    cursor = db.cursor()
    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()
    print("Tables found:", tables)
    db.close()

except Exception as e:
    print("Connection failed:", e)