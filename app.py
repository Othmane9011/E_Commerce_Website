import os
from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
from flask import render_template

app = Flask(__name__, template_folder=os.path.abspath('templates'))
app = Flask(__name__, static_url_path='/static')


mysql = MySQL()

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  
app.config['MYSQL_DB'] = 'tchokafew' 
app.config['MYSQL_PORT'] = 3307  
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql.init_app(app)

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

# Function to insert sample data into 'products' table
def insert_sample_data():
    cur = mysql.connection.cursor()
    cur.execute('INSERT INTO products (name, description, price, inventory) VALUES (%s, %s, %s, %s)', ('Product 1', 'Description of Product 1', 19.99, 100))
    cur.execute('INSERT INTO products (name, description, price, inventory) VALUES (%s, %s, %s, %s)', ('Product 2', 'Description of Product 2', 29.99, 50))

    mysql.connection.commit()
    cur.close()

# Automatically create table and insert sample data when the app starts
with app.app_context():
    create_products_table()
    insert_sample_data()

# Create 'products' table when the app starts
with app.app_context():
    create_products_table()

# Routes for rendering templates
@app.route('/')
def index():
    # Fetch products from the database
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM products')
    products = cur.fetchall()
    cur.close()
    return render_template('index.html', products=products)

@app.route('/product/<int:product_id>')
def product(product_id):
    # Fetch details of a specific product
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    product = cur.fetchone()
    cur.close()
    return render_template('product.html', product=product)

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

        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)