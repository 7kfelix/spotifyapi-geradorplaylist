from flask import Flask, request, redirect, session, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'b3a7c9825c0db75a09e5d4429b7e328a'

sp_oauth = SpotifyOAuth(
    scope="playlist-modify-public",
    client_id=os.getenv('SPOTIPY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
    redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'),
    show_dialog=True,
)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info

    return redirect('/generate')

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        genre = request.form.get('genre').lower()
        quantity = int(request.form.get("quantidade", 10))

        token_info = session.get('token_info', None)
        if not token_info:
            return redirect('/login')
        
        sp = spotipy.Spotify(auth=token_info['access_token'])
        query = f'genre:{genre}'

        results = sp.search(q=query, type='track', limit=quantity)

        musicas = []
        track_ids = []
        limit_per_request = 50
        offset = 0

        while len(musicas) < quantity:
            remaining = quantity - len(musicas)
            limit = min(limit_per_request, remaining)

            results = sp.search(q=query, type='track', limit=limit, offset=offset)
            items = results['tracks']['items']

            if not items:
                break

            for item in results['tracks']['items']:
                nome = item['name']
                artistas = item['artists'][0]['name']
                musicas.append(f'{nome} - {artistas}')
                track_ids.append(item['id'])

            offset += limit

        session['track_ids'] = track_ids
        session['genre'] = genre
        if not items:
            return render_template('generate.html', musicas=[], genre=genre, error="Nenhuma música encontrada para o gênero selecionado.")
        else:
            return render_template('generate.html', musicas=musicas, genre=genre)
    
    return render_template('generate.html')

@app.route('/create_playlist', methods=['POST'])
def create_playlist():
    token_info = session.get('token_info')
    if not token_info:
        return redirect('/login')
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.current_user()['id']
    track_ids = session.get('track_ids', [])
    playlist_name = request.form.get('playlist_name', 'Minha Playlist')

    if not track_ids:
        return redirect('/generate')
    
    playlist = sp.user_playlist_create(user_id, playlist_name, public=True)
    sp.playlist_add_items(playlist_id=playlist['id'], items=track_ids)

    playlist_url = playlist['external_urls']['spotify']
    return render_template('playlist_created.html', url=playlist_url)
