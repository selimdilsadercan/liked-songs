import os
from flask import Flask, redirect, request, session, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import pandas as pd
import json
from urllib.parse import urlencode
import secrets
import time

# Load environment variables - only in development
if os.path.exists('.env'):
    load_dotenv()

app = Flask(__name__)
# Generate a secure random secret key
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))

# Secure session configuration
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# Spotify API credentials
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'https://liked-songs.onrender.com/callback')

if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("Missing Spotify API credentials. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables.")

SCOPE = 'user-library-read'

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_handler=None  # Disable token caching
    )

def get_token():
    token_info = session.get('token_info', None)
    if not token_info:
        return None
    
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    
    if is_expired:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    
    return token_info

@app.route('/logout')
def logout():
    # Clear our session
    session.clear()
    
    # Redirect to Spotify's logout page, then return to our app
    spotify_logout_url = "https://accounts.spotify.com/logout"
    final_url = f"{spotify_logout_url}"
    
    # Return HTML that logs out of Spotify and redirects back
    return f"""
        <script>
            function logout() {{
                // Clear any local storage
                localStorage.clear();
                sessionStorage.clear();
                
                // Logout from Spotify
                fetch('{spotify_logout_url}', {{
                    mode: 'no-cors'
                }}).finally(() => {{
                    // Redirect to home page after a short delay
                    setTimeout(() => {{
                        window.location.href = '/?{time.time()}';
                    }}, 1000);
                }});
            }}
            logout();
        </script>
        <p>Logging out...</p>
    """

@app.route('/')
def index():
    try:
        # Clear any existing session
        session.clear()
        
        # Generate the Spotify login URL with force_login parameter
        sp_oauth = create_spotify_oauth()
        auth_url = sp_oauth.get_authorize_url()
        # Add show_dialog=true to force account selection
        auth_url += "&show_dialog=true"
        
        return f'''
            <h1>Spotify Artist Analyzer</h1>
            <a href="{auth_url}" style="display: inline-block; padding: 10px 20px; background-color: #1DB954; color: white; text-decoration: none; border-radius: 20px; margin: 10px 0;">Login with Spotify</a>
        '''
    except Exception as e:
        app.logger.error(f"Error in index route: {str(e)}")
        return f"An error occurred: {str(e)}", 500

@app.route('/callback')
def callback():
    try:
        sp_oauth = create_spotify_oauth()
        session.clear()
        code = request.args.get('code')
        if not code:
            app.logger.error("No code provided in callback")
            return "Authorization code not found", 400
            
        token_info = sp_oauth.get_access_token(code)
        session["token_info"] = token_info
        return redirect(url_for('analyze'))
    except Exception as e:
        app.logger.error(f"Error in callback route: {str(e)}")
        return f"An error occurred during authentication: {str(e)}", 500

def get_liked_songs(sp):
    """Fetch all liked songs from Spotify"""
    liked_songs = []
    results = sp.current_user_saved_tracks()
    
    while results:
        for item in results['items']:
            track = item['track']
            for artist in track['artists']:
                liked_songs.append({
                    'artist_name': artist['name'],
                    'track_name': track['name']
                })
        
        if results['next']:
            results = sp.next(results)
        else:
            results = None
    
    return liked_songs

def analyze_artists(liked_songs):
    """Analyze the liked songs to count artist occurrences"""
    df = pd.DataFrame(liked_songs)
    artist_counts = df['artist_name'].value_counts()
    total_songs = len(liked_songs)
    artist_percentages = (artist_counts / total_songs * 100).round(2)
    
    analysis = pd.DataFrame({
        'Song Count': artist_counts,
        'Percentage': artist_percentages
    })
    
    return analysis

@app.route('/analyze')
def analyze():
    try:
        token_info = get_token()
        if not token_info:
            return redirect(url_for('index'))
        
        sp = spotipy.Spotify(auth=token_info['access_token'])
        
        # Get user info to display
        user_info = sp.current_user()
        user_name = user_info['display_name']
        
        # Get liked songs
        liked_songs = get_liked_songs(sp)
        
        if not liked_songs:
            return "No liked songs found!"
        
        # Analyze the data
        analysis = analyze_artists(liked_songs)
        
        # Create HTML output with improved styling
        html_output = """
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            table { border-collapse: collapse; width: 100%; max-width: 800px; background-color: white; }
            th, td { padding: 12px; text-align: left; border: 1px solid #ddd; }
            th { background-color: #1DB954; color: white; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            tr:hover { background-color: #f1f1f1; }
            .container { max-width: 800px; margin: 0 auto; padding: 20px; }
            .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
            .button { display: inline-block; padding: 10px 20px; background-color: #1DB954; color: white; 
                     text-decoration: none; border-radius: 20px; }
            .user-info { color: #333; }
        </style>
        <div class="container">
            <div class="header">
                <h1>Your Most Listened Artists</h1>
                <div class="user-info">
                    <p>Logged in as: """ + user_name + """</p>
                    <a href="/logout" class="button">Logout</a>
                </div>
            </div>
        """
        
        html_output += "<table>"
        html_output += "<tr><th>Artist</th><th>Songs</th><th>Percentage</th></tr>"
        
        for artist, row in analysis.iterrows():
            html_output += f"<tr>"
            html_output += f"<td>{artist}</td>"
            html_output += f"<td>{row['Song Count']}</td>"
            html_output += f"<td>{row['Percentage']}%</td>"
            html_output += f"</tr>"
        
        html_output += "</table>"
        html_output += f"<p>Total number of liked songs: {len(liked_songs)}</p>"
        html_output += "</div>"
        
        return html_output
        
    except Exception as e:
        return f"An error occurred: {str(e)}"

if __name__ == '__main__':
    # Development server
    port = int(os.getenv('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    ) 