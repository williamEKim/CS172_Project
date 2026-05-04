import json
import os
import csv

FIELDS = [
    "url", "author_did", "author_handle", "author_display_name",
    "created_at", "indexed_at", "text", "langs",
    "like_count", "repost_count", "reply_count", "quote_count",
    "is_reply", "reply_parent_uri", "url_data"
]

def process_post(post):
    record = post.get("record", {})
    author = post.get("author", {})
    reply = record.get("reply")
    embed = record.get("embed") or {}
    external = embed.get("external", {}) or {}
    url_data = post.get("url_data", [])

    return {
        "url": url_data[0]["url"] if url_data else None,
        "author_did": author.get("did"),
        "author_handle": author.get("handle"),
        "author_display_name": author.get("displayName"),
        "created_at": record.get("createdAt"),
        "indexed_at": post.get("indexedAt"),
        "text": record.get("text"),
        "langs": record.get("langs", []),
        "like_count": post.get("likeCount", 0),
        "repost_count": post.get("repostCount", 0),
        "reply_count": post.get("replyCount", 0),
        "quote_count": post.get("quoteCount", 0),
        "is_reply": reply is not None,
        "reply_parent_uri": reply["parent"]["uri"] if reply else None,
        "url_data": url_data
    }

def save_raw_posts(posts, raw_dir, query):
    os.makedirs(raw_dir, exist_ok=True)
    path = os.path.join(raw_dir, f"raw_{query}.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for post in posts:
            f.write(json.dumps(post) + "\n")

def save_posts(processedPosts, output, query):
    os.makedirs(output, exist_ok=True)

    fileIndex = 0
    curSize = 0
    curFile = None
    curCsv = None
    for post in processedPosts:
        line = json.dumps(post) + "\n"
        lbytes = len(line.encode("utf-8"))
        if curFile is None or curSize + lbytes > 10 * 1024 * 1024:
            if curFile:
                curFile.close()
                curCsv.close()
            jsonlPath = os.path.join(output, f"bluesky_{query}_{fileIndex}.jsonl")
            csvPath = os.path.join(output, f"bluesky_{query}_{fileIndex}.csv")
            curFile = open(jsonlPath, "w", encoding="utf-8")
            curCsv = open(csvPath, "w", newline="", encoding="utf-8")
            curWriter = csv.DictWriter(curCsv, fieldnames=FIELDS)
            curWriter.writeheader()
            fileIndex += 1
            curSize = 0
        curFile.write(line)
        curWriter.writerow(post)
        curSize += lbytes
    if curFile:
        curFile.close()
        curCsv.close()
