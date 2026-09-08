import os
import json
import datetime
import urllib.request
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)
BUNDLED_JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "I told my wife she should embrace her mistakes. She hugged me.",
    "Why don't scientists trust atoms? Because they make up everything.",
    "I'm reading a book on anti-gravity. It's impossible to put down.",
    "Why did the scarecrow win an award? Because he was outstanding in his field.",
    "What do you call a fish with no eyes? A fsh.",
    "Why did the bicycle fall over? Because it was two-tired.",
    "I would tell you a joke about pizza, but it's too cheesy.",
    "How do you organize a space party? You planet.",
    "Why do we tell actors to 'break a leg'? Because every play has a cast.",
]
_joke_cache_date = None
_joke_cache_value = None
def get_daily_joke():
    global _joke_cache_date, _joke_cache_value
    today = datetime.date.today().isoformat()
    if _joke_cache_date == today:
        return _joke_cache_value
    joke = None
    try:
        req = urllib.request.Request(
            'https://v2.jokeapi.dev/joke/Miscellaneous,Pun?blacklistFlags=nsfw,racist,sexist,religious,political,explicit&type=single',
            headers={'User-Agent': 'Mozilla/5.0 (MConnect)'}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            joke = data.get('joke') or None
    except Exception as e:
        print('Joke API unavailable:', e)
    if not joke:
        day_of_year = datetime.date.today().timetuple().tm_yday
        joke = BUNDLED_JOKES[day_of_year % len(BUNDLED_JOKES)]
    _joke_cache_date = today
    _joke_cache_value = joke
    return joke
@app.after_request
def no_cache(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response
DB_URL = os.environ.get('DATABASE_URL', 'postgres://user:password@localhost:5432/outline')
def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS listings (
            id SERIAL PRIMARY KEY,
            category VARCHAR(50) NOT NULL,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2),
            location VARCHAR(255),
            image_url TEXT,
            fields JSONB DEFAULT '{}',
            rating NUMERIC(3, 2) DEFAULT 0,
            rating_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    cur.execute('ALTER TABLE listings ADD COLUMN IF NOT EXISTS rating NUMERIC(3, 2) DEFAULT 0')
    cur.execute('ALTER TABLE listings ADD COLUMN IF NOT EXISTS rating_count INTEGER DEFAULT 0')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            fields JSONB DEFAULT '[]',
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    cur.execute('ALTER TABLE listings DROP CONSTRAINT IF EXISTS listings_category_check')
    cur.execute('SELECT COUNT(*) FROM categories')
    count = cur.fetchone()['count']
    if count == 0:
        defaults = [
            ('hotel', [
                {'name': 'stars', 'label': 'Stars', 'type': 'select', 'options': ['1', '2', '3', '4', '5']},
                {'name': 'amenities', 'label': 'Amenities', 'type': 'text'},
            ]),
            ('car', [
                {'name': 'model', 'label': 'Model', 'type': 'text'},
                {'name': 'seats', 'label': 'Seats', 'type': 'number'},
                {'name': 'year', 'label': 'Year', 'type': 'number'},
            ]),
            ('taxi', [
                {'name': 'rate_per_km', 'label': 'Rate per km', 'type': 'number'},
                {'name': 'area', 'label': 'Area', 'type': 'text'},
                {'name': 'phone', 'label': 'Phone', 'type': 'tel'},
            ]),
        ]
        cur.executemany(
            'INSERT INTO categories (name, fields) VALUES (%s, %s)',
            [(name, json.dumps(fields)) for name, fields in defaults]
        )
    conn.commit()
    cur.close()
    conn.close()
    print('Database initialized')
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')
@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})
@app.route('/api/joke')
def joke():
    return jsonify({
        'joke': get_daily_joke(),
        'date': datetime.date.today().isoformat(),
    })
@app.route('/api/listings', methods=['GET'])
def get_listings():
    conn = get_db()
    cur = conn.cursor()
    category = request.args.get('category')
    search = request.args.get('search')
    query = 'SELECT * FROM listings'
    conditions = []
    values = []
    if category:
        conditions.append(f'category = %s')
        values.append(category)
    if search:
        conditions.append('(name ILIKE %s OR description ILIKE %s OR location ILIKE %s OR category ILIKE %s)')
        val = f'%{search}%'
        values.extend([val, val, val, val])
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    query += ' ORDER BY created_at DESC'
    cur.execute(query, values)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    result = []
    for row in rows:
        row['id'] = row['id']
        row['created_at'] = row['created_at'].isoformat() if row['created_at'] else None
        if row.get('fields') and isinstance(row['fields'], str):
            row['fields'] = json.loads(row['fields'])
        result.append(row)
    return jsonify(result)
@app.route('/api/listings', methods=['POST'])
def create_listing():
    data = request.get_json()
    category = data.get('category')
    name = data.get('name')
    if not category or not name:
        return jsonify({'error': 'Category and name are required'}), 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM categories WHERE name = %s', (category,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({'error': f'Category "{category}" does not exist'}), 400
    cur.execute(
        '''INSERT INTO listings (category, name, description, price, location, image_url, fields)
           VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *''',
        (
            category,
            name,
            data.get('description'),
            data.get('price'),
            data.get('location'),
            data.get('image_url'),
            json.dumps(data.get('fields', {}))
        )
    )
    listing = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    listing['created_at'] = listing['created_at'].isoformat() if listing['created_at'] else None
    if listing.get('fields') and isinstance(listing['fields'], str):
        listing['fields'] = json.loads(listing['fields'])
    return jsonify(listing), 201
@app.route('/api/listings/top', methods=['GET'])
def get_top_listings():
    conn = get_db()
    cur = conn.cursor()
    limit = min(int(request.args.get('limit', 5)), 50)
    cur.execute('SELECT * FROM listings ORDER BY rating DESC, rating_count DESC, created_at DESC LIMIT %s', (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    result = []
    for row in rows:
        row['created_at'] = row['created_at'].isoformat() if row['created_at'] else None
        if row.get('fields') and isinstance(row['fields'], str):
            row['fields'] = json.loads(row['fields'])
        result.append(row)
    return jsonify(result)
@app.route('/api/listings/<int:id>/rate', methods=['POST'])
def rate_listing(id):
    data = request.get_json() or {}
    try:
        value = float(data.get('value'))
    except (TypeError, ValueError):
        return jsonify({'error': 'Rating must be a number'}), 400
    if value < 1 or value > 5:
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT rating, rating_count FROM listings WHERE id = %s', (id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return jsonify({'error': 'Listing not found'}), 404
    old = float(row['rating'] or 0)
    cnt = int(row['rating_count'] or 0)
    new_count = cnt + 1
    new_rating = round((old * cnt + value) / new_count, 2)
    cur.execute('UPDATE listings SET rating = %s, rating_count = %s WHERE id = %s RETURNING rating, rating_count',
                (new_rating, new_count, id))
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'rating': float(updated['rating']), 'rating_count': int(updated['rating_count'])})
@app.route('/api/listings/<int:id>', methods=['GET'])
def get_listing(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM listings WHERE id = %s', (id,))
    listing = cur.fetchone()
    cur.close()
    conn.close()
    if not listing:
        return jsonify({'error': 'Listing not found'}), 404
    listing['created_at'] = listing['created_at'].isoformat() if listing['created_at'] else None
    if listing.get('fields') and isinstance(listing['fields'], str):
        listing['fields'] = json.loads(listing['fields'])
    return jsonify(listing)
@app.route('/api/listings/<int:id>', methods=['PUT'])
def update_listing(id):
    data = request.get_json() or {}
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        '''UPDATE listings
           SET category = %s, name = %s, description = %s, price = %s,
               location = %s, image_url = %s, fields = %s
           WHERE id = %s RETURNING *''',
        (
            data.get('category'),
            name,
            data.get('description'),
            data.get('price'),
            data.get('location'),
            data.get('image_url'),
            json.dumps(data.get('fields', {})),
            id,
        )
    )
    listing = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if not listing:
        return jsonify({'error': 'Listing not found'}), 404
    listing['created_at'] = listing['created_at'].isoformat() if listing['created_at'] else None
    if listing.get('fields') and isinstance(listing['fields'], str):
        listing['fields'] = json.loads(listing['fields'])
    return jsonify(listing)
@app.route('/api/listings/<int:id>', methods=['DELETE'])
def delete_listing(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM listings WHERE id = %s RETURNING *', (id,))
    listing = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if not listing:
        return jsonify({'error': 'Listing not found'}), 404
    return jsonify({'message': 'Listing deleted', 'listing': dict(listing)})
@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM categories ORDER BY id')
    rows = cur.fetchall()
    cur.close()
    conn.close()
    result = []
    for row in rows:
        row['created_at'] = row['created_at'].isoformat() if row['created_at'] else None
        if row.get('fields') and isinstance(row['fields'], str):
            row['fields'] = json.loads(row['fields'])
        result.append(row)
    return jsonify(result)
@app.route('/api/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    name = (data.get('name') or '').strip().lower().replace(' ', '_')
    fields = data.get('fields', [])
    if not name:
        return jsonify({'error': 'Category name is required'}), 400
    if len(name) > 50:
        return jsonify({'error': 'Category name too long'}), 400
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO categories (name, fields) VALUES (%s, %s) RETURNING *',
                    (name, json.dumps(fields)))
        category = cur.fetchone()
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'error': 'Category already exists'}), 400
    cur.close()
    conn.close()
    category['created_at'] = category['created_at'].isoformat() if category['created_at'] else None
    if category.get('fields') and isinstance(category['fields'], str):
        category['fields'] = json.loads(category['fields'])
    return jsonify(category), 201
@app.route('/api/categories/<string:name>', methods=['DELETE'])
def delete_category(name):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM listings WHERE category = %s', (name,))
    deleted_listings = cur.rowcount
    cur.execute('DELETE FROM categories WHERE name = %s RETURNING *', (name,))
    category = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    return jsonify({
        'message': f'Category deleted ({deleted_listings} listing(s) removed)',
        'category': dict(category),
        'listings_removed': deleted_listings,
    })
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=4000, debug=True)
