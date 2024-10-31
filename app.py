from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from kroger import get_access_token, search_products
from database import add_user, get_user, verify_password, add_to_cart_db, update_cart_item, delete_cart_item, get_cart

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flash messages

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if add_user(email, password):
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))  # Redirect to login after successful registration
        else:
            flash('User already exists, please choose a different email.', 'danger')  # Error message

    return render_template('register.html')

# Route to add items to cart in the database
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 403
    
    user_id = session['user_id']
    data = request.get_json()
    product_name = data['name']
    price = data['price']

    add_to_cart_db(user_id, product_name, price)
    return jsonify({"message": f"{product_name} has been added to your cart!"})

# Route to update cart item quantity
@app.route('/update_cart', methods=['POST'])
def update_cart():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 403
    
    user_id = session['user_id']
    data = request.get_json()
    product_name = data['name']
    quantity = data['quantity']

    if quantity > 0:
        update_cart_item(user_id, product_name, quantity)
    else:
        delete_cart_item(user_id, product_name)

    return jsonify({"message": f"{product_name} quantity updated to {quantity}"})

# Route to remove item from cart
@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 403
    
    user_id = session['user_id']
    data = request.get_json()
    product_name = data['name']

    delete_cart_item(user_id, product_name)
    return jsonify({"message": f"{product_name} removed from your cart"})

# Route to view cart
@app.route('/cart')
def view_cart():
    if 'user_id' not in session:
        flash('Please log in to view your cart', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    cart_items = get_cart(user_id)
    total_price = sum(item[1] * item[2] for item in cart_items)
    
    return render_template('cart.html', cart=cart_items, total_price=total_price)

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Retrieve the stored hashed password from the database
        stored_password = get_user(email)

        # Check if the user exists and if the provided password matches the stored hash
        if stored_password and verify_password(stored_password, password):
            session['user_id'] = email  # Store user identifier in session
            flash('Login successful!', 'success')  # Success message
            return redirect(url_for('index'))  # Redirect to home/dashboard page
        else:
            flash('Invalid email or password.', 'danger')  # Error message
            return redirect(url_for('login'))  # Redirect back to login on failure

    return render_template('login.html')

# Existing route for the index (main home page after login)
@app.route('/')
def index():
    token = get_access_token()  # Get the access token from the Kroger API

    # Use search_products to get weekly deals and seasonal items
    seasonal_items = search_products(token, 'halloween')

    # Pass the fetched data to the template
    return render_template('index.html', seasonal_items=seasonal_items)

if __name__ == "__main__":
    app.run(debug=True)
