"""
Routes: home page, episode search (same as before), and chat.
Chat takes natural language input; the LLM first decides whether to use episode search.
If yes, search results are provided as context. If no, the LLM responds directly.
Set API_KEY in your environment before using chat.
"""
import json
import os
import re
from flask import render_template, request, jsonify, Response, stream_with_context
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


def llm_search_decision(client, user_message):
    """
    Ask the LLM whether to search the episode database and, if so, which single word to search.
    Returns (use_search: bool, search_term: str | None). search_term is only used when use_search is True.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You have access to a database of Keeping Up with the Kardashians episode titles, "
                "descriptions, and IMDB ratings. Search is by a single word in the episode title. "
                "The user will ask a question. Reply with exactly: "
                "YES followed by one space and exactly ONE word to search (e.g. YES perfume, YES wedding), "
                "or NO if the question does not need episode data (greetings, meta questions, etc.). "
                "Choose the one word that best matches what to look up in episode titles."
            ),
        },
        {"role": "user", "content": user_message},
    ]
    response = client.chat(messages)
    content = (response.get("content") or "").strip()
    content_upper = content.upper()
    if re.search(r"\bNO\b", content_upper) and not re.search(r"\bYES\b", content_upper):
        return False, None
    yes_match = re.search(r"\bYES\s+(\w+)", content_upper, re.IGNORECASE)
    if yes_match:
        search_term = yes_match.group(1).lower()
        return True, search_term
    if re.search(r"\bYES\b", content_upper):
        # YES but no word found; fallback
        return True, "Kardashian"
    return False, None


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

        api_key = os.getenv("API_KEY")
        if not api_key:
            return jsonify({"error": "API_KEY environment variable not set"}), 500

        client = LLMClient(api_key=api_key)

        # Step 1: LLM decides whether to search and which single word to use
        use_search, search_term = llm_search_decision(client, user_message)

        if use_search:
            # Step 2a: Run search with LLM-chosen term and answer with episode context
            search_query = search_term or "Kardashian"
            episodes_json = json_search(search_query)
            episodes = json.loads(episodes_json)
            context_parts = []
            for ep in episodes:
                context_parts.append(
                    f"Title: {ep['title']}\nDescription: {ep['descr']}\nIMDB Rating: {ep['imdb_rating']}"
                )
            context_text = (
                "\n\n---\n\n".join(context_parts) if context_parts else "No matching episodes found."
            )
            messages = [
                {
                    "role": "system",
                    "content": "You answer questions about Keeping Up with the Kardashians using only the episode information provided. If the information is not in the episodes, say so briefly.",
                },
                {
                    "role": "user",
                    "content": f"Episode information:\n\n{context_text}\n\nUser question: {user_message}",
                },
            ]
        else:
            # Step 2b: Answer without search (general conversation)
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Answer the user's question about Keeping Up with the Kardashians or anything else briefly and conversationally.",
                },
                {"role": "user", "content": user_message},
            ]

        def generate():
            try:
                for chunk in client.chat(messages, stream=True):
                    if chunk.get("content"):
                        yield f"data: {json.dumps({'content': chunk['content']})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

