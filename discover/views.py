import os
import json
from dotenv import load_dotenv
import requests
from django.shortcuts import render
import openai

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')
TMDB_KEY = os.getenv('TMDB_API_KEY')

def get_genres():
    url = "https://api.themoviedb.org/3/genre/movie/list"
    return requests.get(url, params={"api_key": TMDB_KEY}).json().get("genres", [])

def tmdb_search(genre_ids, min_rating, min_length, max_length, min_votes=50):
    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        "api_key":           TMDB_KEY,
        "with_genres":       ",".join(genre_ids),
        "vote_average.gte":  float(min_rating),
        "vote_count.gte":    min_votes,
        "with_runtime.gte":  int(min_length),
        "with_runtime.lte":  int(max_length),
        "sort_by":           "vote_average.desc",
        "page":              1,
    }
    data = requests.get(url, params=params).json().get("results", [])
    return data[:10]  # top 10

def search(request):
    genres = get_genres()
    results = []
    selected = {
        "genre":      [],
        "min_rating": 0,
        "min_length": 0,
        "max_length": 300,
    }

    if request.method == "POST":
        form = request.POST
        selected["genre"]      = form.getlist("genre")
        selected["min_rating"] = float(form["min_rating"])
        selected["min_length"] = int(form["min_length"])
        selected["max_length"] = int(form["max_length"])

        results = tmdb_search(
            genre_ids=selected["genre"],
            min_rating=selected["min_rating"],
            min_length=selected["min_length"],
            max_length=selected["max_length"],
        )

    return render(request, "discover/search.html", {
        "genres":   genres,
        "results":  results,
        "selected": selected,
    })
