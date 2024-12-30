from flask import Flask, jsonify, render_template, request, redirect, url_for
import sqlite3
import requests
import os

app = Flask(__name__)

# Replace with your YouTube Data API key
API_KEY = 'AIzaSyCPggMUGaZFzibbNZXXcWXcegd7UGaLt9E'
BASE_URL = 'https://www.googleapis.com/youtube/v3'
DB_FILE = 'channels.db'

# Database setup
def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE,
                title TEXT
            )
        ''')
        conn.commit()
        conn.close()

@app.route('/')
def home():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM channels')
    channels = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', channels=channels)

@app.route('/add_channel', methods=['POST'])
def add_channel():
    channel_id = request.form['channel_id']

    # Fetch channel details to get the title
    url = f"{BASE_URL}/channels?part=snippet&id={channel_id}&key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'items' in data and len(data['items']) > 0:
            title = data['items'][0]['snippet']['title']
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            try:
                cursor.execute('INSERT INTO channels (channel_id, title) VALUES (?, ?)', (channel_id, title))
                conn.commit()
            except sqlite3.IntegrityError:
                pass  # Channel already exists
            conn.close()
    return redirect(url_for('home'))

@app.route('/delete_channel/<int:id>', methods=['POST'])
def delete_channel(id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM channels WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/api/channel_stats', methods=['GET'])
def get_channel_stats():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT channel_id FROM channels')
    channels = cursor.fetchall()
    conn.close()

    stats = []
    for channel_id, in channels:
        url = f"{BASE_URL}/channels?part=statistics,snippet&id={channel_id}&key={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'items' in data and len(data['items']) > 0:
                item = data['items'][0]
                stats.append({
                    'channel_id': channel_id,
                    'title': item['snippet']['title'],
                    'subscribers': item['statistics'].get('subscriberCount', 'N/A'),
                    'views': item['statistics'].get('viewCount', 'N/A'),
                    'videos': item['statistics'].get('videoCount', 'N/A')
                })
        else:
            stats.append({'channel_id': channel_id, 'error': 'Failed to fetch data'})

    return jsonify(stats)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
