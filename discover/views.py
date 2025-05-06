import os
import json
from dotenv import load_dotenv
import requests
from django.shortcuts import render
import openai

#load .env
load_dotenv()

# Load your keys (or do this in settings.py once globally)
openai.api_key = os.getenv('OPENAI_API_KEY')
TMDB_KEY = os.getenv('TMDB_API_KEY')

def parse_query(text: str) -> dict:
    prompt = (
        "Extract in JSON:\n"
        "- genre (comma-separated)\n"
        "- year_range (start, end)\n"
        f"User: {text}\n"
    )
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )
    return json.loads(resp.choices[0].message.content)

def get_genres():
    url = "https://api.themoviedb.org/3/genre/movie/list"
    return requests.get(url, params={"api_key": TMDB_KEY}).json().get("genres", [])

def tmdb_search(genre_ids, min_rating, max_length):
    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        "api_key": TMDB_KEY,
        "with_genres": ",".join(genre_ids),
        "vote_average.gte": min_rating,
        "with_runtime.lte": max_length,
        "sort_by": "vote_average.desc",
        "page": 1,
    }
    data = requests.get(url, params=params).json().get("results", [])
    return data[:10]  # top 10

def search(request):
    genres = get_genres()
    results = []
    # Default form values
    selected = {
        "genre": [],
        "min_rating": 0,
        "max_length": 300,
    }

    if request.method == "POST":
        form = request.POST
        selected["genre"]      = form.getlist("genre")
        selected["min_rating"] = form["min_rating"]
        selected["max_length"] = form["max_length"]

        # Call TMDb directly (or via an LLM wrapper if you like)
        results = tmdb_search(
            genre_ids=selected["genre"],
            min_rating=selected["min_rating"],
            max_length=selected["max_length"],
        )

    return render(request, "discover/search.html", {
        "genres":   genres,
        "results":  results,
        "selected": selected,
    })
