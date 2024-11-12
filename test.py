import sqlite3
import json

def get_user_orders():
    # Connect to the SQLite database
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Fetch all orders for the given user_id
    cursor.execute('''
        SELECT order_id, order_date, order_status, total_price, items, address, city, state, zip_code, delivery_instructions, payment_status
        FROM orders
        ORDER BY order_date DESC
    ''')

    # Fetch all rows from the query result
    orders = cursor.fetchall()

    conn.close()

    # Process each order and deserialize the items JSON
    order_list = []
    for order in orders:
        try:
            items = json.loads(order[4])  # Deserialize the items field
        except json.JSONDecodeError:
            items = []  # If there's an error in JSON decoding, fallback to empty list

        order_data = {
            'order_id': order[0],
            'order_date': order[1],
            'order_status': order[2],
            'total_price': order[3],
            'items': items,  # This will be a list of items
            'address': order[5],
            'city': order[6],
            'state': order[7],
            'zip_code': order[8],
            'delivery_instructions': order[9],
            'payment_status': order[10]
        }
        order_list.append(order_data)

    return order_list

def print_orders_and_items():
    # Fetch orders for the user
    orders = get_user_orders()

    if not orders:
        print("No orders found.")
        return

    # Print each order's details
    for order in orders:
        print(f"Order ID: {order['order_id']}")
        print(f"Order Date: {order['order_date']}")
        print(f"Order Status: {order['order_status']}")
        print(f"Total Price: ${order['total_price']:.2f}")
        print(f"Delivery Address: {order['address']}, {order['city']}, {order['state']} {order['zip_code']}")
        print(f"Payment Status: {order['payment_status']}")
        print(f"Delivery Instructions: {order['delivery_instructions']}")
        
        # Print items in the order
        print("Items in this order:")
        if order['items']:
            for item in order['items']:
                print(f"  - {item['name']} (x{item['quantity']}) - ${item['price'] * item['quantity']:.2f}")
        else:
            print("  No items found.")

        print("-" * 40)  # Separator line for readability

# Example usage
if __name__ == "__main__":
    
    print_orders_and_items()
