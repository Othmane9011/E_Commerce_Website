import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from flask import render_template
import bcrypt
import mysql.connector



app = Flask(__name__, template_folder=os.path.abspath('templates'))
app = Flask(__name__, static_url_path='/static')
app.secret_key = 'secretkey'


mysql = MySQL()

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  
app.config['MYSQL_DB'] = 'tchokafew' 
app.config['MYSQL_PORT'] = 3306  
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql.init_app(app)


# Function to fetch user email based on user_id
def fetch_user_email(user_id):
    try:
        cur = mysql.connection.cursor()
        query = "SELECT email FROM users WHERE id = %s"
        cur.execute(query, (user_id,))
        user = cur.fetchone()
        cur.close()

        if user:
            return user['email']  # Return the fetched user's email
        else:
            return None  # User with the specified ID not found

    except Exception as e:
        print("Error:", e)
        return None  # Return None in case of an error

    return None

# Function to create the 'users' table if it doesn't exist
def create_users_table():
    cur = mysql.connection.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            password TEXT NOT NULL,
            username VARCHAR(255) NOT NULL  -- Add the 'username' column here
        )
    ''')
    mysql.connection.commit()
    cur.close()

with app.app_context():
    create_users_table()

# Function to create the 'products' table if it doesn't exist
def create_products_table():
    cur = mysql.connection.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            inventory INT NOT NULL
        )
    ''')
    cur.close()

@app.route('/')
def auth_page():
    return render_template('auth.html')

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return 'Passwords do not match. Please try again.'

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO users (email, username, password) VALUES (%s, %s, %s)', (email, username, hashed_password))
        mysql.connection.commit()
        cur.close()

        return redirect('/')

    return render_template('register.html')



@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cur.fetchone()
    cur.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        session['logged_in'] = True
        session['user_id'] = user['id']  # Store user ID in session
        return redirect('/index')  # Redirect to the route rendering index.html after successful login
    else:
        return 'Invalid email or password'

@app.route('/index')
def index():
    if 'logged_in' in session and session['logged_in']:
        user_id = session.get('user_id')

        user_email = fetch_user_email(user_id)

        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM products')
        products = cur.fetchall()
        cur.close()

        return render_template('index.html', products=products, user_email=user_email)
    else:
        return redirect('/')
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Function to insert sample data into 'products' table
def insert_sample_data():
    cur = mysql.connection.cursor()
    cur.execute('INSERT INTO products (name, description, price, inventory) VALUES (%s, %s, %s, %s)', ('Product 1', 'Description of Product 1', 19.99, 100))
    cur.execute('INSERT INTO products (name, description, price, inventory) VALUES (%s, %s, %s, %s)', ('Product 2', 'Description of Product 2', 29.99, 50))
    mysql.connection.commit()
    cur.close()

# Automatically create 'products' table and insert sample data when the app starts
with app.app_context():
    create_products_table()
    insert_sample_data()

# Route to display product details
@app.route('/product/<int:product_id>')
def product(product_id):
    # Fetch details of a specific product
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    product = cur.fetchone()
    cur.close()
    return render_template('product.html', product=product)

# Route to handle checkout
@app.route('/checkout', methods=['POST'])
def checkout():
    # Process order checkout
    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity = request.form['quantity']
        # Process the order, update inventory, etc.
        cur = mysql.connection.cursor()
        cur.execute('UPDATE products SET inventory = inventory - %s WHERE id = %s', (quantity, product_id))
        mysql.connection.commit()
        cur.close()

        return redirect('/')  # Redirect to the main page after checkout

if __name__ == '__main__':
    app.run(debug=True)
    #express js 