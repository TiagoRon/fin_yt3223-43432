import yt_dlp
import sys

ydl_opts_info = {
    'noplaylist': True,
    'quiet': False,
    'cookiefile': 'cookies.txt',
    'extractor_args': {'youtube': ['player_client=android,web']},
}

video_url = "https://www.youtube.com/watch?v=RH4M4YTl4tA"
try:
    with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
        info = ydl.extract_info(video_url, download=False)
        print("Success!", info.get('title'))
except Exception as e:
    print("Error:", e)
