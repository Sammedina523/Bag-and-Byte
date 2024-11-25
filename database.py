import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from kroger import get_access_token, search_products
import json

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

def clear_cart_db(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
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

def create_orders_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS orders')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            order_status TEXT,
            total_price REAL,
            items TEXT,  -- JSON-encoded list of items
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code INTEGER,
            delivery_instructions TEXT,
            payment_status TEXT  -- To store payment status
        )
    ''')
    conn.commit()
    conn.close()

def place_order(user_id, cart_items, total_price, address, city, state, zip_code, delivery_instructions, payment_status):
    try:
        # Open a connection to the SQLite database
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            
            # Serialize the cart items as a JSON string
            items_json = json.dumps(cart_items)
            
            # Insert the order into the orders table
            cursor.execute(''' 
                INSERT INTO orders (user_id, order_status, total_price, items, address, city, state, zip_code, delivery_instructions, payment_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, 'completed', total_price, items_json, address, city, state, zip_code, delivery_instructions, payment_status))
            
            # Commit the transaction (handled automatically by 'with' statement)
            order_id = cursor.lastrowid  # Get the last inserted row's ID (this will be the order_id)
            
            # Return the created order_id
            return order_id
        
    except sqlite3.Error as e:
        # Handle any database errors gracefully
        print(f"An error occurred: {e}")
        return None

# Get all orders for a user
def get_user_orders(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Fetch all orders for the given user_id
    cursor.execute(''' 
        SELECT order_id, order_date, order_status, total_price, items, address, city, state, zip_code, delivery_instructions, payment_status
        FROM orders
        WHERE user_id = ?
        ORDER BY order_date DESC  -- Orders sorted by the most recent
    ''', (user_id,))
    
    orders = cursor.fetchall()
    conn.close()

    # Format the results into a more readable structure
    order_list = []
    for order in orders:
        try:
            items = json.loads(order[4])  # Assuming order[4] is a JSON string
            if not isinstance(items, list):
                print(f"Expected a list but got: {type(items)}")
                items = []  # or handle the error in another way
        except json.JSONDecodeError:
            items = []  # In case the JSON is malformed

        order_data = {
            'order_id': order[0],
            'order_date': order[1],
            'order_status': order[2],
            'total_price': order[3],
            'items': items,  # Deserialize the items JSON string
            'address': order[5],
            'city': order[6],
            'state': order[7],
            'zip_code': order[8],
            'delivery_instructions': order[9],
            'payment_status': order[10]
        }
        order_list.append(order_data)
    
    return order_list

def update_order_status(order_id, new_status):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # Update the order status (from pending to completed)
    cursor.execute('''
        UPDATE orders
        SET order_status = ?
        WHERE order_id = ? AND order_status = 'pending'  -- Make sure we only update pending orders
    ''', (new_status, order_id))
    
    conn.commit()
    conn.close()

# In database.py

def get_order_by_id(order_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Fetch the order by order_id
    cursor.execute(''' 
        SELECT order_id, order_date, order_status, total_price, items, address, city, state, zip_code, delivery_instructions, payment_status
        FROM orders
        WHERE order_id = ?
    ''', (order_id,))

    order = cursor.fetchone()
    conn.close()

    # Check if order exists
    if order:
        try:
            # Deserialize the items from JSON
            items = json.loads(order[4])  # order[4] is the 'items' field
            if not isinstance(items, list):
                print(f"Expected a list but got: {type(items)}")
                items = []  # Handle error if it's not a list
        except json.JSONDecodeError:
            items = []  # In case the JSON is malformed

        # Format the result as a dictionary (similar to get_user_orders)
        order_data = {
            'order_id': order[0],
            'order_date': order[1],
            'order_status': order[2],
            'total_price': order[3],
            'items': items,  # Deserialize the items JSON string
            'address': order[5],
            'city': order[6],
            'state': order[7],
            'zip_code': order[8],
            'delivery_instructions': order[9],
            'payment_status': order[10]
        }

        return order_data
    
    return None  # If no order is found for the given order_id







    
