from flask import Flask, render_template
import requests

app = Flask(__name__)

# Kroger API credentials (replace with your actual credentials)
CLIENT_ID = 'your_client_id'
CLIENT_SECRET = 'your_client_secret'

def get_kroger_token():
    url = 'https://api.kroger.com/v1/connect/oauth2/token'
    data = {
        'grant_type': 'client_credentials',
        'scope': 'product.compact'
    }
    headers = {
        'Authorization': f'Basic {CLIENT_ID}:{CLIENT_SECRET}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(url, data=data, headers=headers)
    response.raise_for_status()
    return response.json()['access_token']

# Fetch products for a given search term (e.g., fruits, vegetables, beverages)
def fetch_products(token, term, limit=10):
    url = f'https://api.kroger.com/v1/products?filter.term={term}&filter.limit={limit}'
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['data']

@app.route('/')
def homepage():
    token = get_kroger_token()

    # Fetch different product categories for the homepage
    fruits = fetch_products(token, 'fruits', limit=5)
    vegetables = fetch_products(token, 'vegetables', limit=5)
    beverages = fetch_products(token, 'beverages', limit=5)

    # Pass all products to the template
    return render_template('index.html', fruits=fruits, vegetables=vegetables, beverages=beverages)

if __name__ == '__main__':
    app.run(debug=True)
