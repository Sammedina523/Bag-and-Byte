from flask import Flask, render_template
import requests

app = Flask(__name__)

CLIENT_ID = 'bagandbyte-2432612430342431786a6a7a4144667543456c792f4433472f6f4f5965785957433762597543636d5752524f6b5554766233664f67703648413533654135037845033016591'
CLIENT_SECRET = 'Yb24nJQRFG8yS73ivzSwTES9cBTfGe39UsjHgEAQ'

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
