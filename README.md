# CS166_Project Social Media Post Scraper

A Python tool to search and collect posts from Bluesky using the AT Protocol API.

## Setup

### Execute Crawler Script
```bash
# Windows
./crawler.bat

# Mac/Linux
source cralwer.sh
```
this will execute everything at once, or you can choose to manually execute the program

### Manual Execution:
### 1. Create and activate a virtual environment

```bash
python3 -m venv venv
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

You should see `(venv)` at the start of your terminal prompt. If you don't, the venv is not active.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the Program

Make sure your venv is activated first, then:

```bash
python main.py
```

**Mac/Linux**
```bash
python -m main
```

You will be prompted for:
1. Your Bluesky handle (e.g. `yourname.bsky.social`)
2. Your Bluesky **App Password** — your regular login password works too, but API password is recommended. Generate one at:
   **Bluesky → Settings → Privacy and Security → App Passwords**
3. A search term (e.g. `basketball`)

## Output (To be implemented)

The scraper collects up to 500MB of posts and saves them in 10MB chunks:
- `bluesky_{query}_{n}.jsonl` — raw JSON, one post per line
- `bluesky_{query}_{n}.csv` — spreadsheet-friendly format

## Updating Dependencies

If you install a new package and want to update `requirements.txt`:

```bash
pip install <new-package>
pip freeze > requirements.txt
```

## Verifying Your Virtual Environment

Check that venv is active:
```bash
which python
```
Should return something like `.../Project_Repo/venv/bin/python`.

Check installed packages:
```bash
pip list
```

If venv is not active, reactivate it:
```bash
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```
