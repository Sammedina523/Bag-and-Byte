import requests
from requests.auth import HTTPBasicAuth
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

# Set up Flask app and SQLAlchemy
app = Flask(__name_)

# PostgreSQL configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://grocery_user:csc190@localhost/grocery_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database model for storing products
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    regular_price = db.Column(db.Numeric(10, 2))
    promo_price = db.Column(db.Numeric(10, 2), nullable=True)
    size = db.Column(db.String(50), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    brand = db.Column(db.String(100), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)

# Create the tables
with app.app_context():
    db.create_all()

# Replace these with your actual Kroger API credentials
CLIENT_ID = 'bagandbyte-2432612430342431786a6a7a4144667543456c792f4433472f6f4f5965785957433762597543636d5752524f6b5554766233664f67703648413533654135037845033016591'
CLIENT_SECRET = 'Yb24nJQRFG8yS73ivzSwTES9cBTfGe39UsjHgEAQ'
TOKEN_URL = 'https://api.kroger.com/v1/connect/oauth2/token'
PRODUCT_API_URL = 'https://api.kroger.com/v1/products'

# Step 1: Get an OAuth 2.0 Access Token
def get_access_token():
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'grant_type': 'client_credentials',
        'scope': 'product.compact',
    }

    response = requests.post(TOKEN_URL, headers=headers, data=data, auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET))

    if response.status_code == 200:
        token_data = response.json()
        return token_data['access_token']
    else:
        print(f"Failed to get access token: {response.status_code}, {response.text}")
        return None

# Step 2: Fetch products from Kroger API
def fetch_products(token, query):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    params = {
        'filter.term': query,
        'filter.locationId': '01234567'  # Replace with a valid location ID
    }

    response = requests.get(PRODUCT_API_URL, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch products: {response.status_code}, {response.text}")
        return None

# Step 3: Save products to the database
def save_products_to_db(products):
    for product in products['data']:
        product_id = product['productId']
        name = product['description']
        regular_price = product['items'][0]['price']['regular']
        promo_price = product['items'][0]['price'].get('promo', None)
        size = product['items'][0].get('size', None)
        category = product.get('category', None)
        brand = product.get('brand', None)
        image_url = None

        # Check for images and get the first front-facing image
        if 'images' in product and len(product['images']) > 0:
            for image in product['images']:
                if image['perspective'] == 'front':  # Using the front image
                    if len(image['sizes']) > 0:
                        image_url = image['sizes'][0]['url']  # Fetch the URL of the first size available
                    break

        # Check if product already exists in the database
        existing_product = Product.query.filter_by(product_id=product_id).first()

        if existing_product:
            # Update existing product
            existing_product.name = name
            existing_product.regular_price = regular_price
            existing_product.promo_price = promo_price
            existing_product.size = size
            existing_product.category = category
            existing_product.brand = brand
            existing_product.image_url = image_url
        else:
            # Insert new product
            new_product = Product(
                product_id=product_id,
                name=name,
                regular_price=regular_price,
                promo_price=promo_price,
                size=size,
                category=category,
                brand=brand,
                image_url=image_url  # Saving the image URL
            )
            db.session.add(new_product)

    db.session.commit()

# Route to update the inventory
@app.route('/update_inventory', methods=['GET'])
def update_inventory():
    token = get_access_token()
    if not token:
        return jsonify({"error": "Unable to retrieve access token"}), 500

    products_data = fetch_products(token, 'milk')  # Example: search for "milk"
    if products_data:
        save_products_to_db(products_data)
        return jsonify({"message": "Inventory updated successfully"}), 200
    else:
        return jsonify({"error": "Failed to fetch products"}), 500

if __name__ == '__main__':
    app.run(debug=True)
