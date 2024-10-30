from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from kroger import get_access_token, search_products
from database import add_user, get_user, verify_password

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

#cart page

# Initialize cart function
def initialize_cart():
    if 'cart' not in session:
        session['cart'] = {}

# Route to add items to cart
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    initialize_cart()
    cart = session['cart']

    # Get product data from JSON request body
    data = request.get_json()
    name = data['name']
    price = data['price']
    
    # Use the product name as a unique key in the cart
    if name in cart:
        cart[name]['quantity'] += 1
    else:
        cart[name] = {
            "name": name,
            "price": price,
            "quantity": 1
        }
    
    # Update session
    session['cart'] = cart
    session.modified = True
    
    return jsonify({"message": f"{name} has been added to your cart!"})

# Route to view cart
@app.route('/cart')
def view_cart():
    initialize_cart()
    cart = session['cart']
    
    # Calculate total price
    total_price = sum(item['price'] * item['quantity'] for item in cart.values())
    return render_template('cart.html', cart=cart, total_price=total_price)


    #cart end

# route for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Retrieve the stored hashed password from the database
        stored_password = get_user(email)

        # Check if the user exists and if the provided password matches the stored hash
        if stored_password and verify_password(stored_password, password):
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
    weekly_deals = search_products(token, 'weekly deals')
    seasonal_items = search_products(token, 'seasonal items')

    # Pass the fetched data to the template
    return render_template('index.html', weekly_deals=weekly_deals, seasonal_items=seasonal_items)

if __name__ == "__main__":
    app.run(debug=True)
