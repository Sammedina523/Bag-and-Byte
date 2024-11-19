from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from database import add_user, get_user, verify_password, add_to_cart_db, update_cart_item, delete_cart_item, get_cart, get_products, get_categories, get_product_by_id, get_suggested_products, get_products_by_query, clear_cart_db, get_user_orders, get_order_by_id, update_order_status, place_order
from database import add_user, get_user, verify_password, add_to_cart_db, update_cart_item, delete_cart_item, get_cart, get_products, get_categories, get_product_by_id, get_suggested_products, get_products_by_query, clear_cart_db, get_user_orders, get_order_by_id, update_order_status, place_order
from kroger import KrogerAPI
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flash messages


@app.route('/search')
def search():
    query = request.args.get('query')
    if query:
        # Search the database for products that match the query
        products = get_products_by_query(query)
        return render_template('search_results.html', products=products, query=query)
    return render_template('search_results.html', products=[], query=query)

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form['confirm_password']
        
         # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        if add_user(email, password):
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('User already exists, please choose a different email.', 'danger')

    return render_template('register.html')

# Route to add items to cart in the database
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 403

    user_id = session['user_id']
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))

    # Get product details from the database
    product = get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    # Add the product to the cart in the database
    add_to_cart_db(user_id, product['name'], product['price'], quantity)
    return jsonify({"message": f"{product['name']} has been added to your cart!"})

@app.route('/product/<int:product_id>')
def product_detail(product_id):

    print(f"Product ID received: {product_id}")

    product = get_product_by_id(product_id)
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('index'))

    suggested_products = get_suggested_products(product['category'])

    return render_template('product_detail.html', product=product, suggested_products=suggested_products)


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
    flash(f"{product_name} has been removed from your cart.", "success")
    
    return jsonify({"message": f"{product_name} removed from your cart"})

# Route to view cart
@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('Please log in to view your cart', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    cart_items = get_cart(user_id)

    # Check if cart_items is a list of dictionaries with 'price' and 'quantity'
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)

    return render_template('cart.html', cart=cart_items, total_price=total_price)


# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        stored_password = get_user(email)

        if stored_password and verify_password(stored_password, password):
            session['user_id'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

# Route to display products with optional category filtering
@app.route('/')
@app.route('/category/<string:category>')
def index(category="All"):
    categories = get_categories()  # Fetch all available categories from the database
    products = get_products(category=category)  # Fetch products filtered by the selected category
    return render_template('index.html', categories=categories, products=products, current_category=category)

# Route to display user profile and cart summary
@app.route('/profile')
@app.route('/profile/<string:category>')
def profile(category="All"):
    if 'user_id' not in session:
        flash('Please log in to access your profile', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    categories = get_categories()
    products = get_products(category=category)  # Filter products based on category
    return render_template('profile.html', categories=categories, products=products, current_category=category)


# Route to display account details
@app.route('/account')
def account():
    if 'user_id' not in session:
        flash('Please log in to access your account', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']

    return render_template('account.html', user_id=user_id)

@app.route('/is_logged_in')
def is_logged_in():
    # Check if the user_id is in the session
    logged_in = 'user_id' in session
    return jsonify({'logged_in': logged_in})


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/checkout')
def checkout():
    states = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", 
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", 
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", 
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", 
    "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", 
    "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", 
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", 
    "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", 
    "Washington", "West Virginia", "Wisconsin", "Wyoming"
    ]
    if 'user_id' not in session:
        flash('Please log in to proceed to checkout', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    cart_items = get_cart(user_id)

    # Calculate total_price by accessing 'price' and 'quantity' keys in cart_items
    total_price = sum(item['price'] * item['quantity'] for item in cart_items)

    return render_template('checkout.html', states=states, cart=cart_items, total_price=total_price)

@app.template_filter('to_12_hour')
def to_12_hour(value):
    try:
        # Convert string to datetime and format to 12-hour time
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S').strftime('%m/%d/%Y %I:%M:%S %p')
    except (ValueError, TypeError):
        return "Invalid Date"

@app.route('/process_checkout', methods=['POST'])
def process_checkout():
    if 'user_id' not in session:
        flash('Please log in to proceed to checkout', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    cart_items = get_cart(user_id)

    # Get the order details from the form
    address = request.form.get('address')
    city = request.form.get('city')
    state = request.form.get('state')
    zip_code = request.form.get('zip_code')
    delivery_instructions = request.form.get('delivery_instructions')
    card_num = request.form.get('card_num')
    exp_date = request.form.get('exp_date')
    cvv = request.form.get('cvv')
    billing_zip = request.form.get('billing_zip')

    # Simple validation for required fields
    if not address or not city or not state or not zip_code:
        flash('Please fill in all required fields for delivery.', 'danger')
        return redirect(url_for('checkout'))

    if not card_num or not exp_date or not cvv or not billing_zip:
        flash('Please provide valid payment information.', 'danger')
        return redirect(url_for('checkout'))

    # Calculate total price from the cart
    total_price = (sum(item['price'] * item['quantity'] for item in cart_items)) * (1.0875) 

    # Place order into the database
    order_id = place_order(
        user_id=user_id,
        cart_items=cart_items,
        total_price=total_price,
        address=address,
        city=city,
        state=state,
        zip_code=zip_code,
        delivery_instructions=delivery_instructions,
        payment_status='Paid'  # In a real application, you'd verify payment through a gateway
    )

    # Clear the cart after order placement
    clear_cart_db(user_id)

    # Flash a success message and redirect to the order confirmation page
    flash(f'Your order #{order_id} has been placed successfully!', 'success')
    orders = get_user_orders(user_id)
    return render_template('orders.html', orders=orders)


# Route to clear all items from the cart
@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 403
    user_id = session['user_id']
    clear_cart_db(user_id)  # Clear the cart in the database
    flash("Your cart has been cleared.", "success")
    return jsonify({"message": "All items have been removed from your cart."})

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        flash('Please log in to view your orders.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Retrieve all orders for the logged-in user
    orders = get_user_orders(user_id)

    return render_template('orders.html', orders=orders)

@app.route('/confirm_order/<int:order_id>', methods=['POST'])
def confirm_order(order_id):
    # Fetch the order from the database using get_user_order_by_id
    order = get_order_by_id(order_id)
    
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('orders'))
    
    # Check if the order is already completed
    if order['order_status'] == 'completed':
        flash('This order has already been completed.', 'info')
        return redirect(url_for('orders'))
    
    # Use the update_order_status function to change the order status to 'Completed'
    update_order_status(order_id, 'completed')

    # Optionally, send a success message and redirect to the orders page
    flash('Order confirmed successfully!', 'success')
    return redirect(url_for('orders'))

@app.route('/reorder/<int:order_id>', methods=['POST'])
def reorder(order_id):
    if 'user_id' not in session:
        flash('Please log in to reorder.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Fetch the original order from the database
    order = get_order_by_id(order_id)
    if not order or order['order_status'] != 'completed':
        flash('Unable to reorder. This order has not been completed.', 'danger')
        return redirect(url_for('orders'))

    # Reorder the items
    reordered_items = order['items']
    
    # Add items back to the cart for the user
    for item in reordered_items:
        add_to_cart_db(user_id, item['name'], item['price'], item['quantity'])

    flash('Your order has been added to the cart for reordering!', 'success')
    return redirect(url_for('cart'))


if __name__ == "__main__":
    app.run(debug=True)