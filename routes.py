"""
Routes: home page, episode search (same as before), and chat.
Chat uses json_search to find Kardashian-related episodes, then sends that context to the LLM.
Set API_KEY in your environment before using chat.
"""
import json
import os
from flask import render_template, request, jsonify
from models import db, Episode, Review
from infosci_spark_client import LLMClient


def json_search(query):
    if not query or not query.strip():
        query = "Kardashian"
    results = db.session.query(Episode, Review).join(
        Review, Episode.id == Review.id
    ).filter(
        Episode.title.ilike(f'%{query}%')
    ).all()
    matches = []
    for episode, review in results:
        matches.append({
            'title': episode.title,
            'descr': episode.descr,
            'imdb_rating': review.imdb_rating
        })
    return json.dumps(matches)


def register_routes(app):
    @app.route("/")
    def home():
        return render_template('base.html')

    # Optional: direct search endpoint (e.g. for debugging).
    @app.route("/episodes")
    def episodes_search():
        text = request.args.get("title", "")
        return json_search(text)

    @app.route("/chat", methods=["POST"])
    def chat():
        data = request.get_json() or {}
        user_message = (data.get("message") or "").strip()
        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        # Use the same search as the template: episodes whose title matches the query.
        # Empty query falls back to "Kardashian" so we still get some episodes.
        search_query = user_message or "Kardashian"
        episodes_json = json_search(search_query)
        episodes = json.loads(episodes_json)

        context_parts = []
        for ep in episodes:
            context_parts.append(f"Title: {ep['title']}\nDescription: {ep['descr']}\nIMDB Rating: {ep['imdb_rating']}")
        context_text = "\n\n---\n\n".join(context_parts) if context_parts else "No matching episodes found."

        api_key = os.getenv("API_KEY")
        if not api_key:
            return jsonify({"error": "API_KEY environment variable not set"}), 500

        client = LLMClient(api_key=api_key)
        messages = [
            {"role": "system", "content": "You answer questions about Keeping Up with the Kardashians using only the episode information provided. If the information is not in the episodes, say so briefly."},
            {"role": "user", "content": f"Episode information:\n\n{context_text}\n\nUser question: {user_message}"}
        ]
        response = client.chat(messages)

        return jsonify({"content": response["content"]})

