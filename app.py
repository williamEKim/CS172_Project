import lucene
import os

lucene.initVM(vmargs=['-Djava.awt.headless=true'])

from flask import Flask, render_template, request, jsonify
from pylucene import create_index, load_posts, advanced_search

app = Flask(__name__)

INDEX_DIR = "bluesky_index"
DATA_DIR = "processed"


@app.before_request
def attach_thread():
    lucene.getVMEnv().attachCurrentThread()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])

    mode = request.args.get("mode", "multi")
    sort_by = request.args.get("sort", "score")
    min_likes = int(request.args.get("min_likes") or 0)
    min_reposts = int(request.args.get("min_reposts") or 0)
    date_from = request.args.get("date_from") or None
    date_to = request.args.get("date_to") or None

    try:
        results = advanced_search(
            INDEX_DIR, q,
            mode=mode,
            sort_by=sort_by,
            min_likes=min_likes,
            min_reposts=min_reposts,
            date_from=date_from,
            date_to=date_to,
        )
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    if not os.path.exists(INDEX_DIR):
        posts = load_posts(DATA_DIR)
        create_index(INDEX_DIR, posts)
    app.run(host='0.0.0.0', debug=True, use_reloader=False, port=5001)
