from flask import Flask, render_template, request, redirect, url_for, flash
from src.kroger import get_access_token, search_products


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flash messages

# Mock user database (for demonstration purposes)
users = {'user@hofstra.edu': 'hofstra'}

# Route for the login screen
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Simple check for a mock user (replace with real database logic later)
        if email in users and users[email] == password:
            flash('Login successful!', 'success')
            return redirect(url_for('index'))  # Redirect to home/dashboard page
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))  # Redirect back to login on failure

    return render_template('login.html')

# Existing route for the index (main home page after login)
@app.route('/')
def index():
    token = get_access_token()  # Get the access token from the Kroger API

    # Use search_products to get weekly deals and seasonal items
    weekly_deals = search_products(token, 'weekly deals')  # Replace 'weekly deals' with the actual search term you want
    seasonal_items = search_products(token, 'seasonal items')  # Replace 'seasonal items' with the actual search term you want

    # Pass the fetched data to the template
    return render_template('index.html', weekly_deals=weekly_deals, seasonal_items=seasonal_items)

if __name__ == "__main__":
    app.run(debug=True)
