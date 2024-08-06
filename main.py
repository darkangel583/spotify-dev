from flask import Flask, redirect, request, jsonify, session, url_for, render_template
import urllib.parse
import requests
import datetime

app = Flask(__name__)

app.secret_key = 'inoinroieno_f43fnveoirmkveooe'

CLIENT_ID = '20ccab6278f345a797cac34e1607a633'
CLIENT_SECRET = '460367b8786f4dffad4ad5e15040b335'
REDIRECT_URI = 'http://localhost:5000/callback'
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    scope = 'user-library-read user-read-private user-read-email playlist-modify-private playlist-modify-public'
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})
    
    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        # Log token info for debugging
        print("Token info:", token_info)

        session['access_token'] = token_info.get('access_token')
        session['refresh_token'] = token_info.get('refresh_token')
        session['expires_at'] = datetime.datetime.now().timestamp() + token_info.get('expires_in', 0)
        
        if not session['access_token']:
            return jsonify({"error": "Failed to obtain access token"}), 400

        return redirect(url_for('liked_songs'))

@app.route('/liked-songs')
def liked_songs():
    if 'access_token' not in session:
        return redirect(url_for('login'))
    
    if datetime.datetime.now().timestamp() > session['expires_at']:
        return redirect(url_for('refresh_token'))
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    all_songs = []
    limit = 50  # Maximum number of items per request
    offset = 0  # Start from the beginning

    while True:
        response = requests.get(API_BASE_URL + f'me/tracks?limit={limit}&offset={offset}', headers=headers)
        data = response.json()
        all_songs.extend(data['items'])
        if len(data['items']) < limit:
            break
        offset += limit

    return render_template('liked_songs.html', songs=all_songs)


@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect(url_for('login'))
    
    req_body = {
        'grant_type': 'refresh_token',
        'refresh_token': session['refresh_token'],
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, data=req_body)
    new_token_info = response.json()
    session['access_token'] = new_token_info['access_token']
    session['expires_at'] = datetime.datetime.now().timestamp() + new_token_info['expires_in']

    return redirect(url_for('liked_songs'))

@app.route('/create-playlist')
def create_playlist():
    if 'access_token' not in session:
        return redirect(url_for('login'))

    if datetime.datetime.now().timestamp() > session['expires_at']:
        return redirect(url_for('refresh_token'))

    headers = {
        'Authorization': f"Bearer {session['access_token']}",
        'Content-Type': 'application/json'
    }

    # Fetch the user's profile to get the user_id
    response = requests.get(API_BASE_URL + 'me', headers=headers)
    if response.status_code != 200:
        return jsonify({"error": f"Failed to fetch user profile: {response.status_code} - {response.text}"}), response.status_code

    user_data = response.json()
    user_id = user_data.get('id')
    if not user_id:
        return jsonify({"error": "Failed to fetch user ID"}), 400

    # Create a new playlist
    playlist_name = "My Liked Songs"
    playlist_description = "A playlist containing all my liked songs."
    playlist_data = {
        'name': playlist_name,
        'description': playlist_description,
        'public': False  # You can set this to True if you want the playlist to be public
    }
    response = requests.post(f"{API_BASE_URL}users/{user_id}/playlists", headers=headers, json=playlist_data)
    
    # Log the response and error details
    if response.status_code != 201:  # 201 Created
        return jsonify({"error": f"Failed to create playlist: {response.status_code} - {response.text}"}), response.status_code
    
    playlist = response.json()
    if 'id' not in playlist:
        return jsonify({"error": "Failed to create playlist: Missing 'id' in response"}), 400

    return redirect(url_for('add_songs_to_playlist', playlist_id=playlist['id']))


@app.route('/add-songs-to-playlist/<playlist_id>')
def add_songs_to_playlist(playlist_id):
    if 'access_token' not in session:
        return redirect(url_for('login'))

    if datetime.datetime.now().timestamp() > session['expires_at']:
        return redirect(url_for('refresh_token'))

    headers = {
        'Authorization': f"Bearer {session['access_token']}",
        'Content-Type': 'application/json'
    }

    all_songs = []
    limit = 50
    offset = 0

    # Fetch all liked songs
    while True:
        response = requests.get(API_BASE_URL + f'me/tracks?limit={limit}&offset={offset}', headers=headers)
        data = response.json()
        all_songs.extend(data['items'])
        if len(data['items']) < limit:
            break
        offset += limit

    # Get the URIs of the songs
    track_uris = [song['track']['uri'] for song in all_songs]

    # Add songs to the playlist in batches of 100 (max allowed per request)
    for i in range(0, len(track_uris), 100):
        batch = track_uris[i:i+100]
        requests.post(f"{API_BASE_URL}playlists/{playlist_id}/tracks", headers=headers, json={'uris': batch})

    return redirect(url_for('share_playlist', playlist_id=playlist_id))

@app.route('/share-playlist/<playlist_id>')
def share_playlist(playlist_id):
    if 'access_token' not in session:
        return redirect(url_for('login'))

    playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"
    return render_template('share_playlist.html', playlist_url=playlist_url)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
