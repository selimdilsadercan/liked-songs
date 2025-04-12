import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import pandas as pd
from collections import Counter

# Load environment variables
load_dotenv()

# Spotify API credentials
CLIENT_ID = "6919a60a626649ac92d20341b1445ac1"
CLIENT_SECRET = "bd192c6c1dbd4aa6864e1e8988622ba5"
REDIRECT_URI = 'http://localhost:8888/callback'

# Define the scope for accessing liked songs
SCOPE = 'user-library-read'

def authenticate_spotify():
    """Authenticate with Spotify API"""
    auth_manager = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    )
    return spotipy.Spotify(auth_manager=auth_manager)

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
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(liked_songs)
    
    # Count artist occurrences
    artist_counts = df['artist_name'].value_counts()
    
    # Calculate total number of songs
    total_songs = len(liked_songs)
    
    # Calculate percentage for each artist
    artist_percentages = (artist_counts / total_songs * 100).round(2)
    
    # Create a DataFrame with counts and percentages
    analysis = pd.DataFrame({
        'Song Count': artist_counts,
        'Percentage': artist_percentages
    })
    
    return analysis

def main():
    try:
        # Authenticate with Spotify
        print("Authenticating with Spotify...")
        sp = authenticate_spotify()
        
        # Get liked songs
        print("Fetching your liked songs...")
        liked_songs = get_liked_songs(sp)
        
        if not liked_songs:
            print("No liked songs found!")
            return
        
        # Analyze the data
        print("Analyzing your music taste...")
        analysis = analyze_artists(liked_songs)
        
        # Display results
        print("\nYour Most Listened Artists:")
        print("===========================")
        for artist, row in analysis.iterrows():
            print(f"{artist}:")
            print(f"  Songs: {row['Song Count']}")
            print(f"  Percentage: {row['Percentage']}%")
            print("---------------------------")
        
        print(f"\nTotal number of liked songs: {len(liked_songs)}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 