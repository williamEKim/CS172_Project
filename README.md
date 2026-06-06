# CS172 Project — Bluesky Sports Search Engine

Sports and social media generate a large amount of content, making it difficult for users to quickly locate relevant information. Our project aims to address that by building a search engine over a large collection of sports-related posts from Bluesky. The system gathers posts from a variety of topics, processes the data, and indexes the collection with PyLucene. Using a Flask-based interface, users can search across content, author information, and linked page titles. 

---

## System Overview

### Architecture

```
Bluesky API → main.py (crawler) → processed/*.jsonl
                                        ↓
                                  pylucene.py (indexer)
                                        ↓
                                  bluesky_index/ (Lucene index on disk)
                                        ↓
                                   app.py (Flask)
                                        ↓
                               templates/index.html (Web UI)
```

### Index Structure

We are using PyLucene to index the sports dataset that we collected in Part A. After parsing the JSON objects, we convert each post into a Lucene document and add the document to the bluesky_index/ directory using IndexWriter. Each document contains text data for searching, metadata for display, and numeric data for sorting and filtering.

Numeric fields such as like_count, repost_count, reply_count, and quote_count are indexed separately. Time stamps are converted into epoch values to enable date range queries and sorting in chronological order. 

Each document contains 16 fields across 5 categories:

**Identifiers** — `url`, `author_did`, `author_handle` stored as exact-match meta fields.

**Author** — `author_display_name` stored as a tokenised text field, searchable by name terms.

**Post Content** — `text` (main searchable body), `langs` (multi-value language codes).

**Timestamps**
- `created_at`, `indexed_at` — ISO strings stored for display
- `created_at_epoch` — Unix timestamp stored as `LongPoint + StoredField`, enables date-based sorting and range filtering

**Engagement**
- `like_count`, `repost_count`, `reply_count`, `quote_count` — stored as strings for display
- `like_count_int`, `repost_count_int`, `reply_count_int`, `quote_count_int` — stored as `IntPoint` for numeric filtering and ranking

**Reply / Links** — `is_reply`, `reply_parent_uri`, `link_title` (searchable), `link_url`, `link_status` (multi-value)

### Search & Ranking

The search algorithm supports two modes: `multi-field search` and `single-field search`. 
- In multi-field mode, the user query is searched across the fields author_display_name, text, and link_title. A document is retrieved if the user's query matches any of these fields.
- In single field mode, the user query is searched over the text field only.

Users can also refine their searches by applying filters such as a date range, minimum like count, and minimum repost count. The retrieved documents are then ranked using BM25. The results are returned in descending order based on the user's selected sorting method.

The web interface supports:

- **Single-field mode** — searches the `text` field only
- **Multi-field mode** — searches `text`, `author_display_name`, and `link_title` simultaneously using `MultiFieldQueryParser`
- **Sort by relevance** — default BM25 score, descending
- **Sort by date** — re-sorted by `created_at_epoch` after retrieval
- **Sort by likes** — re-sorted by `like_count` after retrieval
- **Filters** — minimum likes, minimum reposts, date range (using `LongPoint` and `IntPoint` range queries)


### LLM Summarization (Extra Credit)

LLM summarization uses Google’s Gemini API. The summarization itself is dictated by the prompt passed into the API to compress each query post into 5 bulletpoints. We added new functionality to the crawler’s code which allows users to skip the crawling process and jump straight to the summarization process. The console prompts the user for the directory of the JSON files for each post, desired directory for where the summarizations should be saved, and Gemini API key. The summarization goes through each query and for each query, it handles each post before moving on to the next query. Summarizations are stored via text file and saved into the directory defined by the user.

---

## Limitations
Some limits of the system currently include:
- Exact keyword matching may end up missing posts that are related 
- Duplicate results may appear if multiple queries retrieve overlapping posts 
- New posts are not included in the dataset until they have been recollected and reindexed 
- Summarization feature is limited to top post per query for speed, requires payment to be fully functional

---

## Deployment Instructions

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- A [Bluesky](https://bsky.app/) account (for crawling)
- (Optional) A [Gemini API](https://aistudio.google.com/) key (for summarization)

---

### Option 1: One-Touch Execution (Recommended)

Since the data is already collected and pre-processed in the repo, you only need Docker Desktop running. The script builds the index and launches the web interface automatically.

**Mac/Linux:**
```bash
bash indexer.sh processed
```

**Windows:**
```bat
indexer.bat processed
```

Then open your browser and go to:
```
http://localhost:5001
```

> **Note:** If port 5001 is already in use, change the port mapping in `docker-compose.yml` (e.g. `5002:5001`) and access the corresponding port.

---

### Option 2: Manual Setup

#### (Optional) Step 1 — Web Crawling and Processing Data

Since we have already executed the web-crawler and pre-processed the collected data (they are all in the repo), **this step is optional for the demo/testing**.

```bash
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
pip install -r requirements.txt
python3 main.py
```

You will be prompted for your Bluesky handle, app password, and output directory. Processed posts are saved to `processed/`.

#### Step 2 — Start the Docker Container

**Mac/Linux:**
```bash
cd /path/to/Project_Repo
docker run -it -v "$(pwd):/app" -p 5001:5001 coady/pylucene bash
```

**Windows:**
```bat
docker run -it -v "%cd%:/app" -p 5001:5001 coady/pylucene bash
```

#### Step 3 — Build The Index (first time only)

Inside the container:
```bash
cd /app
python3 pylucene.py
```

This creates `bluesky_index/` in your project folder. Skip this step on subsequent runs if the index already exists.

#### Step 4 — Run The Flask App

Inside the container:
```bash
pip install flask
python3 app.py
```

#### Step 5 — Open The Search Web-Interface

Open your browser and go to:
```
http://localhost:5001
```

---

## Crawler Scripts

To re-collect data from Bluesky:

**Mac/Linux:**
```bash
cd crawler/
source crawler.sh
```

**Windows:**
```bat
cd crawler/
crawler.bat
```

---

## Output Files

| Path | Description |
|------|-------------|
| `processed/bluesky_{query}_{n}.jsonl` | Cleaned posts, one per line |
| `raw/raw_{query}.jsonl` | Unprocessed raw JSON from Bluesky API |
| `bluesky_index/` | PyLucene index directory (persisted on disk) |
| `/summaries/{query}_summary.txt` | Gemini-generated post summaries |

---

## Managing Dependencies

```bash
pip install <new-package>
pip freeze > requirements.txt
```

---

## Troubleshooting

**`import lucene` fails outside Docker:**
PyLucene cannot be installed via pip. Use the Docker container as described above.

**Port already in use:**
Change the port mapping in `docker-compose.yml` (e.g. `5002:5001`) and access `localhost:5002`. On Mac, port 5000 is reserved by AirPlay Receiver.

**`No .jsonl files found in processed/`:**
Run `main.py` first to collect and process posts before running the indexer.

**Gemini 429 errors:**
You have exceeded the free tier rate limit. Wait for the quota to reset (midnight Pacific time) and rerun. The daily limit is 1500 requests.
