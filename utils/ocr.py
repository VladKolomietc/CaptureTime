import json
import os 
from google import genai 
from google.genai import types 

def extract_data_from_img(img):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    promt = """
    Analyze this lock screen screenshot. Extract the time tracking data and the currently playing music.
    Return ONLY a valid JSON object.
    {
        "captured_at": "DD.MM.YYYY", 
        "focus_time": "HH:MM",
        "music_title": "Song name or null if no music is playing",
        "author": "Author name or null if no music is playing"
    }
    """

    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=[promt, img],
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )

    return json.loads(response.text.strip())