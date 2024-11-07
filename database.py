import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from kroger import get_access_token, search_products

# User management functions
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

# Cart management functions
def create_cart_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            user_id TEXT,
            product_name TEXT,
            price REAL,
            quantity INTEGER,
            PRIMARY KEY (user_id, product_name)
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

def get_products_by_query(query):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Use a LIKE query to find products with names that contain the search query
    cursor.execute("SELECT product_id, name, price, image_url FROM products WHERE name LIKE ?", ('%' + query + '%',))
    products = cursor.fetchall()
    conn.close()
    # Convert to a list of dictionaries for easier rendering
    return [{'product_id': row[0], 'name': row[1], 'price': row[2], 'image_url': row[3]} for row in products]

def delete_cart_item(user_id, product_name):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cart WHERE user_id = ? AND product_name = ?', (user_id, product_name))
    conn.commit()
    conn.close()

# In database.py
def get_cart(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT products.name, cart.price, cart.quantity, products.image_url
        FROM cart
        JOIN products ON cart.product_name = products.name
        WHERE cart.user_id = ?
    ''', (user_id,))
    cart_items = cursor.fetchall()
    conn.close()
    return [{'name': row[0], 'price': row[1], 'quantity': row[2], 'image_url': row[3]} for row in cart_items]


# Product management functions
def create_products_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS products')  # Drop the existing table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            name TEXT,
            price REAL,
            image_url TEXT,
            category TEXT
        )
    ''')
    conn.commit()
    conn.close()



def fetch_and_store_products(query=''):
    token = get_access_token()
    if not token:
        print("Failed to get access token.")
        return

    products_data = search_products(token, query)
    if not products_data or 'data' not in products_data:
        print("No products found or an error occurred.")
        return

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    for product in products_data['data']:
        # Strip leading zeros from product_id
        product_id = int(product.get('productId').lstrip('0')) if product.get('productId') else None

        # Print the product ID for debugging
        print(f"Storing product: ID={product_id}, Name={product.get('description')}")

        name = product.get('description')
        price = product['items'][0].get('price', {}).get('regular') if product.get('items') else None
        image_url = product['images'][0]['sizes'][0]['url'] if product.get('images') else None
        category = product.get('categories', ["Uncategorized"])[0]

        cursor.execute('''
            INSERT OR REPLACE INTO products (product_id, name, price, image_url, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (product_id, name, price, image_url, category))

    conn.commit()
    conn.close()
    print("Products have been successfully stored in the database.")


def get_products(category=None):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    if category and category != 'All':
        cursor.execute('SELECT product_id, name, price, image_url FROM products WHERE category = ?', (category,))
    else:
        cursor.execute('SELECT product_id, name, price, image_url FROM products')
        
    products = cursor.fetchall()
    conn.close()
    return [{'product_id': row[0], 'name': row[1], 'price': row[2], 'image_url': row[3]} for row in products]


def get_product_by_id(product_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT product_id, name, price, image_url, category FROM products WHERE product_id = ?', (product_id,))
    product = cursor.fetchone()
    conn.close()

    if product:
        print("Product found:", product)  # Debug line
        return {
            'product_id': product[0],
            'name': product[1],
            'price': product[2],
            'image_url': product[3],
            'category': product[4]
        }
    
    print("No product found")  # Debug line
    return None

def get_suggested_products(category):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT product_id, name, price, image_url FROM products WHERE category = ? LIMIT 5', (category,))
    products = cursor.fetchall()
    conn.close()
    return [{'product_id': row[0], 'name': row[1], 'price': row[2], 'image_url': row[3]} for row in products]

# Function to get all unique categories from products table
def get_categories():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT category FROM products')
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    return categories

# Initialize tables if running this file
if __name__ == "__main__":
    create_cart_table()
    create_products_table()
    print("Cart and products tables created successfully.")
    fetch_and_store_products(query="candy")
    fetch_and_store_products(query="produce")
    fetch_and_store_products(query="fruits")
    fetch_and_store_products(query="dairy")
    fetch_and_store_products(query="frozen")
    fetch_and_store_products(query="breads")
    print("Fetched and stored products.")
    print("Available categories:", get_categories())
