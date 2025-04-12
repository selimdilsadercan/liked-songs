# Spotify Artist Analyzer

This Python application analyzes your Spotify liked songs to find your most listened-to artists.

## Setup

1. Create a Spotify Developer account at https://developer.spotify.com
2. Create a new application in the Spotify Developer Dashboard
3. Get your Client ID and Client Secret from the application settings
4. Create a `.env` file with the following content:
   ```
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   ```
5. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the script:

```
python spotify_analyzer.py
```

The first time you run the script, it will open your browser for Spotify authentication. After authenticating, the script will:

1. Fetch all your liked songs
2. Count the occurrences of each artist
3. Display a sorted list of your most listened-to artists
