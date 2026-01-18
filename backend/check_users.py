import sqlite3

conn = sqlite3.connect('gharmitra.db')
cursor = conn.cursor()

cursor.execute('SELECT email, role FROM users LIMIT 5')
users = cursor.fetchall()

print('Available users:')
for email, role in users:
    print(f'  {email} ({role})')

conn.close()
