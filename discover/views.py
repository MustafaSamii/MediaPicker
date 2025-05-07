import os
import json
from pathlib import Path

import requests
import openai
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render

# 1) Load .env (assuming .env sits next to manage.py)
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# 2) Pull your keys from env
openai.api_key = os.getenv("OPENAI_API_KEY")
TMDB_KEY        = os.getenv("TMDB_API_KEY")

# 3) Helper to talk to TMDb
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
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json().get("results", [])[:10]

# 4) The AJAX chat endpoint
@csrf_exempt
def chat(request):
    # Retrieve past conversation from session
    history = request.session.get("history", [])

    # Parse incoming JSON
    body     = request.body.decode("utf-8") or "{}"
    payload  = json.loads(body)
    user_msg = payload.get("message", "")

    # Append user message to history
    history.append({"role": "user", "content": user_msg})

    # Build the LLM prompt
    prompt = [
        {"role": "system",
         "content": "You’re a movie matchmaker. The user will tell you what they like/dislike."}
    ] + history

    # Call ChatCompletion
    resp      = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=prompt,
        temperature=0.7,
    )
    bot_reply = resp.choices[0].message.content

    # Save assistant reply in history (keep only last 10)
    history.append({"role": "assistant", "content": bot_reply})
    request.session["history"] = history[-10:]

    # Try to parse JSON instructions out of the bot’s reply
    try:
        parsed = json.loads(bot_reply)
    except json.JSONDecodeError:
        parsed = {}

    # If the bot gave us genres, ratings, and runtimes, fetch movies
    if parsed.get("genres"):
        results = tmdb_search(
            genre_ids  = parsed["genres"],
            min_rating = parsed.get("min_rating", 0),
            min_length = parsed.get("min_length", 0),
            max_length = parsed.get("max_runtime", 300),
        )
    else:
        results = []

    # Render those into a chunk of HTML
    reply_html = ""
    for m in results:
        poster = (f"https://image.tmdb.org/t/p/w154{m['poster_path']}"
                  if m.get("poster_path") else "")
        reply_html += f"""
          <div class="bot-bubble mb-3">
            {'<img src="'+poster+'" class="me-2 rounded" />' if poster else ''}
            <strong>{m['title']}</strong><br>
            ⭐ {m['vote_average']} — ⏳ {m.get('runtime','?')} min
          </div>
        """

    return JsonResponse({"reply": reply_html})

def get_genres():
    url = "https://api.themoviedb.org/3/genre/movie/list"
    return requests.get(url, params={"api_key": TMDB_KEY}) \
                   .json().get("genres", [])

def search(request):
    genres   = get_genres()
    results  = []
    selected = {
        "genre":      [],
        "min_length": 0,
        "max_length": 300,
    }

    if request.method == "POST":
        form = request.POST
        selected["genre"]      = form.getlist("genre")
        selected["min_length"] = form.get("min_length", 0)
        selected["max_length"] = form.get("max_length", 300)

        results = tmdb_search(
            genre_ids  = selected["genre"],
            min_rating = form.get("min_rating", 0),
            min_length = selected["min_length"],
            max_length = selected["max_length"],
        )

    return render(request, "discover/search.html", {
        "genres":   genres,
        "results":  results,
        "selected": selected,
    })

# discover/views.py

def search(request):
    genres   = get_genres()
    results  = []
    selected = {
        "genre":      [],
        "min_length": 0,
        "max_length": 300,
        "min_rating": 0.0,
    }

    if request.method == "POST":
        form = request.POST
        selected["genre"]      = form.getlist("genre")
        selected["min_length"] = int(form.get("min_length", 0))
        selected["max_length"] = int(form.get("max_length", 300))

        # Coerce rating default to 0.0 if empty
        raw_rating = form.get("min_rating") or "0"
        selected["min_rating"] = float(raw_rating)

        results = tmdb_search(
            genre_ids  = selected["genre"],
            min_rating = selected["min_rating"],
            min_length = selected["min_length"],
            max_length = selected["max_length"],
        )

    return render(request, "discover/search.html", {
        "genres":   genres,
        "results":  results,
        "selected": selected,
    })

