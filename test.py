from mysql.connector import connect

conn = connect(
    host="127.0.0.1",
    user="root",
    password="1234",
    database="work_allocation",
    port=3306
)
cursor = conn.cursor()
cursor.execute("SELECT DATABASE();")
print(cursor.fetchone())
conn.close()
