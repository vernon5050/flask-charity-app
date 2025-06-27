import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from werkzeug.utils import secure_filename
# from serverless_http import serverless  # Required for Vercel
from serverless_wsgi import handle_request 

# Initialize Flask app
app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper: Connect to database
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Helper: Check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route: Home page (display unsold items)
@app.route("/")
def index():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items WHERE sold = 0').fetchall()
    conn.close()
    return render_template('index.html', items=items)

# Route: Handle donation
@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        donor = request.form.get('donor', 'Anonymous')
        charity = request.form.get('charity', 'General Fund')

        # Handle image upload
        image = request.files.get('image')
        filename = None
        if image and image.filename != '' and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Insert donation into database
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO items (name, description, price, donor, charity, image, sold)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (name, description, price, donor, charity, filename))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('donate.html')

# Route: Serve uploaded image files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Route: Buy item page
@app.route('/buy/<int:item_id>')
def buy(item_id):
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM items WHERE id = ?', (item_id,)).fetchone()
    conn.close()

    if item is None or item['sold']:
        return "Item not available", 404

    return render_template('buy.html', item=item)

# Route: Mark item as sold (AJAX/POST)
@app.route('/mark_sold/<int:item_id>', methods=['POST'])
def mark_sold(item_id):
    conn = get_db_connection()
    conn.execute('UPDATE items SET sold = 1 WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# Vercel serverless handler
# handler = serverless(app)
handler = handle_request(app)  # New handler for Vercel

# Run the Flask app locally if not in Vercel environment
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
