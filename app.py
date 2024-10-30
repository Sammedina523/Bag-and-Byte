from flask import Flask, render_template, request, redirect, url_for, flash
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
    seasonal_items = search_products(token, 'chips')

    # Pass the fetched data to the template
    return render_template('index.html', seasonal_items=seasonal_items)

if __name__ == "__main__":
    app.run(debug=True)
