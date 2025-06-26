import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items WHERE sold = 0').fetchall()
    conn.close()
    return render_template('index.html', items=items)

@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        donor = request.form['donor']
        price = float(request.form['price'])
        conn = get_db_connection()
        conn.execute('INSERT INTO items (name, description, donor, price) VALUES (?, ?, ?, ?)',
                     (name, description, donor, price))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('donate.html')
    
    UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        # Handle form submission
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        donor = request.form.get('donor', 'Anonymous')
        charity = request.form['charity']
        
        # Handle file upload
        image = request.files['image']
        filename = None
        
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Add to database
        new_item = Item(name=name, description=description, price=price, 
                       donor=donor, charity=charity, image=filename)
        db.session.add(new_item)
        db.session.commit()
        
        return redirect(url_for('index'))
    
    return render_template('donate.html')  # Or redirect to index if you're using the inline form

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/buy/<int:item_id>')
def buy(item_id):
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM items WHERE id = ?', (item_id,)).fetchone()
    conn.close()
    if item is None or item['sold']:
        return "Item not available", 404
    return render_template('buy.html', item=item)

@app.route('/mark_sold/<int:item_id>', methods=['POST'])
def mark_sold(item_id):
    conn = get_db_connection()
    conn.execute('UPDATE items SET sold = 1 WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
