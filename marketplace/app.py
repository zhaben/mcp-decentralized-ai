from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_FILE = "market.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            listed_price REAL NOT NULL,
            ai_agent_address TEXT NOT NULL,
            owner_name TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id INTEGER NOT NULL,
            offer_price REAL NOT NULL,
            buyer_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'accepted', 'rejected'
            FOREIGN KEY(listing_id) REFERENCES listings(id)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/listings', methods=['POST'])
def create_listing():
    data = request.json
    item_name = data.get('item_name')
    listed_price = data.get('listed_price')
    ai_agent_address = data.get('ai_agent_address')
    owner_name = data.get('owner_name')
    if not all([item_name, listed_price, ai_agent_address, owner_name]):
        return jsonify({'error': 'All fields are required'}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO listings (item_name, listed_price, ai_agent_address, owner_name)
        VALUES (?, ?, ?, ?)
    ''', (item_name, listed_price, ai_agent_address, owner_name))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Listing created'}), 201

@app.route('/listings', methods=['GET'])
def get_listings():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM listings')
    rows = cursor.fetchall()
    conn.close()
    listings = [{
        'id': row[0],
        'item_name': row[1],
        'listed_price': row[2],
        'ai_agent_address': row[3],
        'owner_name': row[4]
    } for row in rows]
    return jsonify(listings)

@app.route('/offers', methods=['GET'])
def get_offers():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT offers.id, offers.listing_id, offers.offer_price, offers.buyer_name, offers.status,
               listings.item_name, listings.owner_name
        FROM offers
        JOIN listings ON offers.listing_id = listings.id
    ''')
    rows = cursor.fetchall()
    conn.close()

    offers = []
    for row in rows:
        offer = {
            'id': row[0],
            'listing_id': row[1],
            'offer_price': row[2],
            'buyer_name': row[3],
            'status': row[4],
            'item_name': row[5],
            'current_owner': row[6]
        }
        offers.append(offer)

    return jsonify(offers)

@app.route('/offers', methods=['POST'])
def create_offer():
    data = request.json
    listing_id = data.get('listing_id')
    offer_price = data.get('offer_price')
    buyer_name = data.get('buyer_name')
    if not all([listing_id, offer_price, buyer_name]):
        return jsonify({'error': 'All fields are required'}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM listings WHERE id = ?', (listing_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Listing not find'}), 404

    cursor.execute('''
        INSERT INTO offers (listing_id, offer_price, buyer_name)
        VALUES (?, ?, ?)
    ''', (listing_id, offer_price, buyer_name))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Offer created'}), 201

@app.route('/offers/<int:offer_id>', methods=['POST'])
def respond_to_offer(offer_id):
    data = request.json
    action = data.get('action')  # 'accept' or 'reject'

    if action not in ['accept', 'reject']:
        return jsonify({'error': 'Non valid action'}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('SELECT listing_id, buyer_name, status FROM offers WHERE id = ?', (offer_id,))
    offer = cursor.fetchone()
    if not offer:
        conn.close()
        return jsonify({'error': 'Offer not found'}), 404

    listing_id, buyer_name, status = offer

    if status != 'pending':
        conn.close()
        return jsonify({'error': 'Offer already terminated'}), 400

    cursor.execute('UPDATE offers SET status = ? WHERE id = ?', (action, offer_id))

    if action == 'accept':
        cursor.execute('UPDATE listings SET owner_name = ? WHERE id = ?', (buyer_name, listing_id))
    
    conn.commit()
    conn.close()
    return jsonify({'message': f'Offer executed'}), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
