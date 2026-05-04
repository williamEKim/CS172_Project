# CS166 Project — Social Media Post Scraper
Sports and social media are an integral part of American culture. However, with busy schedules and a demand for faster-paced content consumption, consuming long pieces of information can be tiresome for many. This project aims to solve this problem by using LLMs to transform large clusters of sports-related information into bite-sized bits that are easier to comprehend. In other words, we aim to build a crawler that collects sports-related information from BlueSky and then uses a reliable and fast LLM to summarize these posts. 

---

## Setup

### Option 1: Automated Script (Recommended)
Run the crawler script to handle everything at once:

**Mac/Linux:**
```bash
source crawler.sh
```

**Windows:**
```bat
crawler.bat
```

### Option 2: Manual Setup

#### 1. Create a virtual environment
```bash
python3 -m venv venv
```

#### 2. Activate the virtual environment

**Mac/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bat
venv\Scripts\activate
```

You should see `(venv)` at the start of your terminal prompt. If you don't, the venv is not active.

#### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## Running the Program
Make sure your venv is activated first, then:

**Mac/Linux:**
```bash
python3 main.py
```

**Windows:**
```bat
python main.py
```

You will be prompted for:
1. Your Bluesky handle (e.g. `yourname.bsky.social`)
2. Your Bluesky **App Password** — your regular login password works, but an App Password is recommended.
   Generate one at: **Bluesky → Settings → Privacy and Security → App Passwords**
3. A search term (e.g. `basketball`)

---

## Output
The scraper collects up to 500MB of posts and saves them in 10MB chunks:

| File | Description |
|------|-------------|
| `bluesky_{query}_{n}.jsonl` | Raw JSON, one post per line |
| `bluesky_{query}_{n}.csv` | Spreadsheet-friendly format |

---

## Managing Dependencies

If you install a new package and want to update `requirements.txt`:
```bash
pip install <new-package>
pip freeze > requirements.txt
```

---

## Troubleshooting

**Check that your venv is active:**
```bash
which python  # Mac/Linux — should return .../venv/bin/python
```

**Check installed packages:**
```bash
pip list
```

**Reactivate venv if needed:**
```bash
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```
