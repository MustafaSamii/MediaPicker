import os
import json
import requests
from django.shortcuts import render
import openai

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

def tmdb_search(parsed: dict) -> list:
    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        "api_key": TMDB_KEY,
        "with_genres": parsed.get("genre", ""),
        "primary_release_date.gte": f"{parsed.get('year_range',[0])[0]}-01-01",
        "primary_release_date.lte": f"{parsed.get('year_range',[0,0])[1]}-12-31",
    }
    data = requests.get(url, params=params).json()
    return data.get("results", [])

def search(request):
    """
    Renders the search page with optional 'results' context.
    """
    query = request.GET.get('q')
    results = []
    if query:
        parsed = parse_query(query)
        results = tmdb_search(parsed)
    return render(request, 'discover/search.html', {
        'results': results,
        'query': query,
    })
