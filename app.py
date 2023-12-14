import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from flask import render_template
import bcrypt
import mysql.connector
import base64
from werkzeug.utils import secure_filename




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


def create_products_table():
    cur = mysql.connection.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            inventory INT NOT NULL,
            category VARCHAR(255) NOT NULL,
            image_path VARCHAR(255) NOT NULL
        )
    ''')
    mysql.connection.commit()
    cur.close()


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

@app.route('/manage')
def manage():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM products')
    products = cur.fetchall()
    cur.close()

    return render_template('manage.html', products=products)

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

        return render_template('index.html', user_email=user_email)
    else:
        return redirect('/')
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/manage')
def manage_products():
    return render_template('manage.html')


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
            # Use secure_filename to prevent any unsafe characters in the filename
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

            # Save the image path to the database
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
    
@app.route('/modify_product/<int:product_id>', methods=['POST'])
def modify_product(product_id):
    if request.method == 'POST':
        new_name = request.form['name']
        new_price = request.form['price']
        new_inventory = request.form['inventory']
        new_category = request.form['category']
        new_description = request.form['description']
        # Fetch other modified attributes similarly

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

@app.route('/product_list')
def product_list():
    products = get_products()  # Fetch product data from the database
    return render_template('product_list.html', products=products)

if __name__ == '__main__':
    app.run(debug=True)
    #express js 