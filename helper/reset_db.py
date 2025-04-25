import sqlite3

def reset_db():
    # Connect to the SQLite database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Drop the 'users' table if it exists
    cursor.execute('DROP TABLE IF EXISTS users')

    # Recreate the 'users' table with the correct schema, including new fields
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            email_phone_hash TEXT NOT NULL,
            prefer_time TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            contact_timestamp DATETIME,
            response TEXT -- Allow NULL
        )
    ''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    print("Database reset successfully")

if __name__ == '__main__':
    reset_db()