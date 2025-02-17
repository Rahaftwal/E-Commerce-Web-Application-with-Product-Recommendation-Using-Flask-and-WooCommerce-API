from flask import Flask, render_template, redirect, url_for, session, request # type: ignore
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from woocommerce import API
import os
from dotenv import load_dotenv

import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# WooCommerce API configuration using environment variables
wcapi = API(
    url=os.getenv('WOOCOMMERCE_URL'),
    consumer_key=os.getenv('WOOCOMMERCE_CONSUMER_KEY'),
    consumer_secret=os.getenv('WOOCOMMERCE_CONSUMER_SECRET'),
    version="wc/v3"
)

# Dummy user store (for the purpose of login management only)
users = {}

class User(UserMixin):
    def __init__(self, email):
        self.id = email

@login_manager.user_loader
def load_user(user_id):
    return User(user_id) if user_id in users else None

@app.route('/')
def index():
    # Get all products from WooCommerce API
    response = wcapi.get("products", params={"per_page": 100})  # Increase per_page to get more products
    products = response.json()
    
    # Add string ID for consistency
    for product in products:
        product['id_str'] = str(product['id'])
    
    return render_template('index.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Implement actual login logic here
        user_obj = User(email)
        login_user(user_obj)
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        city = request.form['city']
        password = request.form['password']


        user_data = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "password": password,
            "billing": {
                "phone": phone,
                "city": city
            }
        }
        response = wcapi.post("customers", user_data)
        if response.status_code == 201:
            users[email] = {'password': password}
            user_obj = User(email)
            login_user(user_obj)
            return redirect(url_for('index'))
        else:
            error_message = response.json().get('message', 'Unknown error')
            return f"Error creating user: {error_message}", 400
    return render_template('signup.html')



@app.route('/add_to_wishlist/<product_id>')
def add_to_wishlist(product_id):
    favorites = session.get('favorites', [])
    if product_id not in favorites:
        favorites.append(product_id)
    else:
        favorites.remove(product_id)
    session['favorites'] = favorites
    return 'success'  # Return a simple success message

@app.route('/remove_from_wishlist/<product_id>')
def remove_from_wishlist(product_id):
    favorites = session.get('favorites', [])
    if product_id in favorites:
        favorites.remove(product_id)
    session['favorites'] = favorites
    return redirect(url_for('favorites'))

@app.route('/favorites')
def favorites():
    favorites = session.get('favorites', [])
    response = wcapi.get("products")
    products = {str(product['id']): product for product in response.json()}
    return render_template('favorites.html', favorites=favorites, products=products)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    """
    Add product to shopping cart:
    - Accepts product data via POST request
    - Stores product info in session
    - Returns success message
    """
    product_data = request.json
    cart = session.get('cart', [])
    product_list = [
        product_data['product_id'],
        product_data['product_name'],
        product_data['product_image'],
        float(product_data['product_price']),
        int(product_data['quantity'])
    ]
    cart.append(product_list)
    session['cart'] = cart
    return 'Product added to cart'


@app.route('/cart')
def cart():
    cart = session.get('cart', [])
    total_price = 0.0
    for item in cart:
        try:
            quantity = int(item[4])
            price = float(item[3])
            total_price += quantity * price
            product_id = item[0]
        except (ValueError, KeyError, IndexError) as e:
            print(f"Error calculating total for item: {item}. Error: {e}")
            continue
    return render_template('cart.html', cart=cart, total_price=total_price)


@app.route('/remove_from_cart/<int:item_index>', methods=['POST'])
def remove_from_cart(item_index):
    cart = session.get('cart', [])
    if 0 <= item_index < len(cart):
        cart.pop(item_index)
        session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/product/<product_id>')
def product_detail(product_id):
    response = wcapi.get(f"products/{product_id}")
    product = response.json()
    variations_response = wcapi.get(f"products/{product_id}/variations")
    variations = variations_response.json()
    product['variations'] = variations
    cart = session.get('cart', [])
    total_price = 0.0
    for item in cart:
        try:
            quantity = int(item[4])
            price = float(item[3])
            total_price += quantity * price
            product_id = item[0]
        except (ValueError, KeyError, IndexError) as e:
            print(f"Error calculating total for item: {item}. Error: {e}")
            continue
    return render_template('product_detail.html', product=product, cart=cart, total_price=total_price)



@app.route('/order-confirmation')
def order_confirmation():
    return render_template('order_confirmation.html')



@app.route('/my-account', methods=['GET', 'POST'])
@login_required
def my_account():

    response = wcapi.get(f"customers?email={current_user.id}")
    user_data = response.json()

    if not user_data:
        return "User not found", 404

    user_info = user_data[0]

    if request.method == 'POST':

        updated_data = {
            "first_name": request.form['first_name'],
            "last_name": request.form['last_name'],
            "billing": {
                "phone": request.form['phone'],
                "city": request.form['city'],
                "country": request.form['country']
            }
        }

        update_response = wcapi.put(f"customers/{user_info['id']}", updated_data)
        if update_response.status_code == 200:
            return redirect(url_for('my_account'))
        else:
            return f"Error updating user: {update_response.json().get('message')}", 400

    return render_template('my_account.html', user=user_info)


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', [])
    print(f"Cart Contents: {cart}")  # Print cart contents for debugging
    total_price = 0.0
    line_items = []
    purchased_tags = session.get('purchased_tags', set())  # Get previous purchased tags from session

    for item in cart:
        try:
            # Assuming the item structure is [product_id, name, image_url, price, quantity]
            product_id = item[0]
            quantity = int(item[4])
            price = float(item[3])
            if not product_id:
                raise ValueError("Product ID is missing")
            total_price += quantity * price
            line_items.append({
                'product_id': product_id,
                'quantity': quantity
            })


            # Get the product details to extract tags
            product_response = wcapi.get(f"products/{product_id}")
            product_data = product_response.json()
            for tag in product_data['tags']:
                if isinstance(purchased_tags, set):
                    purchased_tags.add(tag['id'])  # Use add for set
                elif isinstance(purchased_tags, list):
                    purchased_tags.append(tag['id'])  # Use append for list


        except (ValueError, KeyError, IndexError) as e:
            print(f"Error processing item: {item}. Error: {e}")
            continue

    session['purchased_tags'] = list(purchased_tags)  # Store the tags in the session
    print(f"Line Items: {line_items}")

    if request.method == 'POST':
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        phone = request.form.get('phone', '')
        email = request.form.get('email', '')
        address1 = request.form.get('address1', '')
        address2 = request.form.get('address2', '')
        region = request.form.get('region', '')
        country = request.form.get('country', '')

        order_data = {
            "payment_method": "cod",
            "payment_method_title": "Cash on Delivery",
            "set_paid": False,
            "billing": {
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
                "email": email,
                "address_1": address1,
                "address_2": address2,
                "city": "",
                "state": region,
                "postcode": "",
                "country": country
            },
            "shipping": {
                "first_name": first_name,
                "last_name": last_name,
                "address_1": address1,
                "address_2": address2,
                "city": "",
                "state": region,
                "postcode": "",
                "country": country
            },
            "line_items": line_items,
        }

        # Log order data for debugging
        print("Order Data:", json.dumps(order_data, indent=4))

        response = wcapi.post("orders", order_data)

        # Log response details for debugging
        print(f"Status Code: {response.status_code}")
        print(f"Response Content: {response.json()}")

        if response.status_code == 201:
            session.pop('cart', None)
            return redirect(url_for('order_confirmation'))
        else:
            error_message = response.json().get('message', 'Unknown error')
            return f"Error creating order: {error_message}", 400

    user_info = None
    if current_user.is_authenticated:
        response = wcapi.get(f"customers?email={current_user.email}")
        user_data = response.json()
        if user_data:
            user_info = user_data[0]

    return render_template('checkout.html', cart=cart, total_price=total_price, user=user_info)

if __name__ == "__main__":
    app.run(debug=True)
