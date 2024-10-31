import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def add_user(email, password):
    hashed_password = generate_password_hash(password)  # Hash the password
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        return False  # User already exists
    finally:
        conn.close()
    return True

def get_user(email):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

def verify_password(stored_password, provided_password):
    return check_password_hash(stored_password, provided_password)

def create_cart_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            user_id TEXT,
            product_name TEXT,
            price REAL,
            quantity INTEGER,
            PRIMARY KEY (user_id, product_name)  -- Composite primary key
        )
    ''')
    conn.commit()
    conn.close()

def add_to_cart_db(user_id, product_name, price, quantity=1):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO cart (user_id, product_name, price, quantity)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, product_name) 
        DO UPDATE SET quantity = quantity + ?
    ''', (user_id, product_name, price, quantity, quantity))
    conn.commit()
    conn.close()

def update_cart_item(user_id, product_name, quantity):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE cart SET quantity = ? WHERE user_id = ? AND product_name = ?', (quantity, user_id, product_name))
    conn.commit()
    conn.close()

def delete_cart_item(user_id, product_name):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cart WHERE user_id = ? AND product_name = ?', (user_id, product_name))
    conn.commit()
    conn.close()

def get_cart(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT product_name, price, quantity FROM cart WHERE user_id = ?', (user_id,))
    cart_items = cursor.fetchall()
    conn.close()
    return cart_items

if __name__ == "__main__":
    create_cart_table()
    print("Cart table created successfully.")