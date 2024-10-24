import requests
from requests.auth import HTTPBasicAuth

# Replace these with your actual Kroger API credentials
CLIENT_ID = 'bagandbyte-2432612430342431786a6a7a4144667543456c792f4433472f6f4f5965785957433762597543636d5752524f6b5554766233664f67703648413533654135037845033016591'
CLIENT_SECRET = 'Yb24nJQRFG8yS73ivzSwTES9cBTfGe39UsjHgEAQ'

# OAuth 2.0 token URL and Kroger API product search URL
TOKEN_URL = 'https://api.kroger.com/v1/connect/oauth2/token'
PRODUCT_API_URL = 'https://api.kroger.com/v1/products'

# Step 1: Get an OAuth 2.0 Access Token
def get_access_token():
    # Request headers and data for token generation
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'grant_type': 'client_credentials',
        'scope': 'product.compact',  # Scope for product data
    }

    # Send the POST request to obtain an access token
    response = requests.post(TOKEN_URL, headers=headers, data=data, auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET))

    if response.status_code == 200:
        token_data = response.json()
        return token_data['access_token']
    else:
        print(f"Failed to get access token: {response.status_code}, {response.text}")
        return None

# Step 2: Search for Products Using Kroger API
def search_products(token, query):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    params = {
        'filter.term': query,  # Search term, e.g., "milk"
        'filter.locationId': '01400943'  # Replace with a valid location ID
    }

    # Send the GET request to search for products
    response = requests.get(PRODUCT_API_URL, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch products: {response.status_code}, {response.text}")
        return None

def display_products_with_images(products):
    for product in products['data']:
        product_id = product['productId']
        name = product['description']

        # Check for images and get the first available image (front perspective)
        image_url = None
        if 'images' in product and len(product['images']) > 0:
            for image in product['images']:
                if image['perspective'] == 'front':  # Use front-facing image
                    if len(image['sizes']) > 0:
                        image_url = image['sizes'][0]['url']  # Fetch the URL of the first size available
                    break

        print(f"Product ID: {product_id}")
        print(f"Name: {name}")
        if image_url:
            print(f"Image URL: {image_url}")
        else:
            print("No image available.")
        print("-" * 40)



# Main code to test the API
if __name__ == "__main__":
    # Step 1: Get Access Token
    token = get_access_token()
    if token:
        print(f"Access token: {token}")

        # Step 2: Search for products (e.g., search for "milk")
        products = search_products(token, 'milk')
        if products:
             display_products_with_images(products)
        else:
            print("No products found or an error occurred.")
    else:
        print("Failed to get access token.")
