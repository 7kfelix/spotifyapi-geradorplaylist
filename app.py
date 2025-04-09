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

        token_info = session.get('token_info', None)
        if not token_info:
            return redirect('/login')
        
        sp = spotipy.Spotify(auth=token_info['access_token'])

        query = f'genre:{genre}'

        results = sp.search(q=query, type='track', limit=10)

        musicas = []
        for item in results['tracks']['items']:
            nome = item['name']
            artistas = item['artists'][0]['name']
            musicas.append(f'{nome} - {artistas}')

        return render_template('generate.html', musicas=musicas, genre=genre)
    
    return render_template('generate.html')
