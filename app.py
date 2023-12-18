import os
from flask import Flask, render_template, request, redirect, jsonify, url_for, session
from flask_mysqldb import MySQL
from flask import render_template
import bcrypt
import mysql.connector
import base64
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin


app = Flask(__name__, template_folder=os.path.abspath('templates'))
app = Flask(__name__, static_url_path='/static')
app.secret_key = 'secretkey'

UPLOAD_FOLDER = 'static/product_images'

mysql = MySQL()

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'tchokafew'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mysql.init_app(app)


login_manager = LoginManager()
login_manager.init_app(app)
users = {
    1: {'id': 1, 'email': 'user@example.com', 'username': 'user', 'password': bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt())}
}


# Function to fetch user email based on user_id
def fetch_user_email(user_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT email FROM users WHERE id = %s"
        cur.execute(query, (user_id,))
        user = cur.fetchone()
        cur.close()

        if user:
            return user['email']
        else:
            return None

    except Exception as e:
        print("Error:", e)
        return None


@app.context_processor
def inject_user_name():
    user_name = None
    if current_user.is_authenticated:
        user_id = current_user.get_id()
        try:
            cur = mysql.connection.cursor()
            cur.execute('SELECT username FROM users WHERE id = %s', (user_id,))
            user = cur.fetchone()
            cur.close()

            if user:
                user_name = user['username']
        except Exception as e:
            print("Error:", e)

    return dict(user_name=user_name)


@app.route('/')
def auth_page():
    return render_template('login.html')


class User(UserMixin):
    def __init__(self, user_id, email, password):
        self.id = user_id
        self.email = email
        self.password = password

    @staticmethod
    def get_by_email(email):
        try:
            cur = mysql.connection.cursor()
            query = "SELECT id, email, password FROM users WHERE email = %s"
            cur.execute(query, (email,))
            user = cur.fetchone()
            cur.close()

            if user:
                return User(user['id'], user['email'], user['password'])
            else:
                return None

        except Exception as e:
            print("Error:", e)
            return None

    @staticmethod
    def get_by_id(user_id):
        try:
            cur = mysql.connection.cursor()
            query = "SELECT id, email, password FROM users WHERE id = %s"
            cur.execute(query, (user_id,))
            user = cur.fetchone()
            cur.close()

            if user:
                return User(user['id'], user['email'], user['password'])
            else:
                return None

        except Exception as e:
            print("Error:", e)
            return None


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = bcrypt.hashpw(
            request.form['password'].encode('utf-8'), bcrypt.gensalt())

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users (email, username, password) VALUES (%s, %s, %s)",
                    (email, username, password))
        mysql.connection.commit()

        cur.close()

        return redirect('/login')

    return render_template('register.html')


@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)


@app.route('/manage')
def manage():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM products')
    products = cur.fetchall()
    cur.close()

    return render_template('manage.html', products=products)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.get_by_email(email)

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            login_user(user)
            return redirect('/index')

        return 'Invalid email or password'

    return render_template('login.html')


@app.route('/index')
def index():
    if 'logged_in' in session and session['logged_in']:
        user_id = session.get('user_id')
        user_email = fetch_user_email(user_id)

        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM products WHERE visibility = 1')
        products = cur.fetchall()
        cur.close()

        return render_template('index.html', user_email=user_email, products=products)
    else:
        return redirect('/')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@app.route('/manage')
def manage_products():
    return render_template('manage.html')


# Adding a product to the database using the manage page
@app.route('/add_product', methods=['POST'])
def add_product():

    if request.method == 'POST':

        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        inventory = int(request.form['inventory'])
        category = request.form['category']

        image = request.files['image']
        if image.filename == '':
            return 'No selected file'

        if image:

            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

            cur = mysql.connection.cursor()
            cur.execute('''
                INSERT INTO products (name, description, price, inventory, category, image_path)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (name, description, price, inventory, category, image_path))
            mysql.connection.commit()
            cur.close()

            return redirect('/manage')
        else:
            return 'Image upload failed'
    else:
        return 'Invalid request method'

# Modification of the products
@app.route('/modify_product/<int:product_id>', methods=['POST'])
def modify_product(product_id):
    if request.method == 'POST':
        new_name = request.form['name']
        new_price = request.form['price']
        new_inventory = request.form['inventory']
        new_category = request.form['category']
        new_description = request.form['description']

        cur = mysql.connection.cursor()
        cur.execute('''
            UPDATE products 
            SET name = %s, 
                price = %s, 
                inventory = %s, 
                category = %s,
                description = %s
            WHERE id = %s
        ''', (new_name, new_price, new_inventory, new_category, new_description, product_id))
        mysql.connection.commit()
        cur.close()

        return redirect('/manage')
    else:
        return 'Invalid request method'


# Disable or enable visibility of a product from the manage page
@app.route('/toggle_visibility/<int:product_id>', methods=['POST'])
def toggle_visibility(product_id):
    update_query = "UPDATE products SET visibility = 1 WHERE id = %s"
    cur = mysql.connection.cursor()
    cur.execute(update_query, (product_id,))
    mysql.connection.commit()
    cur.close()

    return '', 204

# mange page disabllle or enablle
@app.route('/disable_visibility/<int:product_id>', methods=['POST'])
def disable_visibility(product_id):
    update_query = "UPDATE products SET visibility = 0 WHERE id = %s"
    cur = mysql.connection.cursor()
    cur.execute(update_query, (product_id,))
    mysql.connection.commit()
    cur.close()

    return '', 204


#add to cart
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):

    user_id = current_user.get_id()

    if user_id:
        try:
            cur = mysql.connection.cursor()

            cur.execute(
                'SELECT name, description, price, inventory, category, image_path FROM products WHERE id = %s', (product_id,))
            product_info = cur.fetchone()

            if product_info:

                cur.execute(
                    'SELECT * FROM cart WHERE user_id = %s AND product_id = %s', (user_id, product_id))
                existing_item = cur.fetchone()

                if existing_item:

                    new_quantity = existing_item['quantity'] + 1
                    cur.execute('UPDATE cart SET quantity = %s WHERE user_id = %s AND product_id = %s', (
                        new_quantity, user_id, product_id))
                else:

                    cur.execute('INSERT INTO cart (user_id, product_id, quantity, name, description, price, inventory, category, image_path) VALUES (%s, %s, 1, %s, %s, %s, %s, %s, %s)',
                                (user_id, product_id, product_info['name'], product_info['description'], product_info['price'], product_info['inventory'], product_info['category'], product_info['image_path']))

                mysql.connection.commit()
                cur.close()

                return redirect('/cart')
            else:
                return 'Product not found', 404
        except Exception as e:
            print("Error:", e)
            return 'Error adding product to cart', 500
    else:
        return redirect('/login')


#view cart
@app.route('/cart')
@login_required
def view_cart():

    user_id = current_user.get_id()

    if user_id:
        try:
            cur = mysql.connection.cursor()
            cur.execute('''
                SELECT products.name, products.description, products.price, products.inventory, products.category, products.image_path, cart.quantity 
                FROM cart 
                JOIN products ON cart.product_id = products.id 
                WHERE cart.user_id = %s
            ''', (user_id,))
            cart_items = cur.fetchall()
            cur.close()


            total_items = sum(item['quantity'] for item in cart_items)
            total_price = sum(item['price'] * item['quantity']
                              for item in cart_items)

            return render_template('cart.html', cart_items=cart_items, total_items=total_items, total_price=total_price)
        except Exception as e:
            print("Error:", e)

            return 'Error fetching cart items', 500
    else:
        return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
    # express js
