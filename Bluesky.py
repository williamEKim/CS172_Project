import requests
import time
import json, os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from urllib.parse import urlparse
from bs4 import BeautifulSoup

def login(handle, password):
    auth_response = requests.post(
        "https://bsky.social/xrpc/com.atproto.server.createSession",
        json={"identifier": handle, "password": password}
    )

    if auth_response.status_code != 200:
        print("Login failed:", auth_response.text)
        exit()

    token = auth_response.json()["accessJwt"]
    print("Logged in successfully!")
    return token



def fetch_posts(token, query, target_bytes, handle, password):
    # without headers, API request returned 403 Forbidden
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "BlueskySearchBot/1.0"
    }

    cursor = None
    total_bytes = 0
    post_count = 0

    print(f"\nFetching posts about '{query}'...\n")

    while total_bytes < target_bytes:
        params = {"q": query, "limit": 100}
        if cursor:
            params["cursor"] = cursor

        response = requests.get(
            "https://api.bsky.app/xrpc/app.bsky.feed.searchPosts",
            params=params,
            headers=headers
        )

        if response.status_code != 200:
            try:
                error = response.json()
            except:
                print("Error:", response.text)
                break

            if error.get("error") == "ExpiredToken":
                print("Token expired. Re-authenticating...")

                if not handle or not password:
                    raise Exception("Failed to retrieve credentials")
                
                token = login(handle, password)
                headers["Authorization"] = f"Bearer {token}"

                continue

            print("Error:", error)
            break

        data = response.json()
        posts = data.get("posts", [])
        cursor = data.get("cursor")

        if not posts:
            print("No more posts available.")
            break

        for post in posts:
            yield post
            total_bytes += len(str(post).encode("utf-8"))
            post_count += 1

        print(f"Posts fetched: {post_count} | Data collected: {total_bytes / 1024 / 1024:.2f} MB")

        if not cursor:
            print("Reached end of search results.")
            break

        time.sleep(0.5)



def extract_urls(post):
    urls = []

    facets = post.get("record", {}).get("facets", [])
    for facet in facets:
        features = facet.get("features", [])
        for feature in features:
            if feature.get("$type") == "app.bsky.richtext.facet#link":
                try:
                    urls.append(feature.get("uri"))
                except:
                    print("Cannot extract url")

    embed = post.get("record", {}).get("embed", {})
    external = embed.get("external") or post.get("embed", {}).get("external")
    if external and external.get("uri"):
        try:
            urls.append(external["uri"])
        except:
            print("Cannot extract url")

    urls = list(dict.fromkeys(urls))

    post["url_data"] = [
        {"url": url, "title": "", "status": 0}
        for url in urls
    ]



def fetch_title_for_item(item, headers, total_urls, progress, lock, domain_lock, domain_next_available, min_delay):
    url = item.get("url")

    with lock:
        progress["count"] += 1
        current = progress["count"]

    print(f"\n{current}/{total_urls} Processing URL: {url}")

    parsed = urlparse(url or "")
    domain = parsed.netloc.lower() if parsed.netloc else None
    if domain:
        with domain_lock:
            now = time.time()
            available_at = domain_next_available.get(domain, now)
            if available_at > now:
                wait = available_at - now
                domain_next_available[domain] = available_at + min_delay
            else:
                wait = 0
                domain_next_available[domain] = now + min_delay
        if wait > 0:
            print(f"Waiting {wait:.2f}s before requesting {domain}")
            time.sleep(wait)

    if not url:
        item["status"] = 0
        item["title"] = ""
        return

    if "bit.ly" in url:
        print("Skipping bit.ly links")
        item["status"] = 0
        item["title"] = ""
        return

    try:
        t0 = time.time()
        print(" START CONNECTION")

        response = requests.get(
            url,
            timeout=(3, 5),
            headers=headers,
            allow_redirects=True,
            stream=True
        )

        print(f" CONNECTION FINISHED ({time.time() - t0:.2f}s)")
        print(" STATUS:", response.status_code)

        if response.status_code != 200:
            item["status"] = 0
            item["title"] = ""
            return

        t1 = time.time()
        content_type = response.headers.get("Content-Type", "")
        print(f" HEADERS READ ({time.time() - t1:.2f}s)")

        if "text/html" not in content_type:
            item["status"] = 0
            item["title"] = ""
            return

        t2 = time.time()
        print(" READING BODY")

        html = response.content
        print(f" BODY READ ({time.time() - t2:.2f}s)")

        soup = BeautifulSoup(html, "html.parser")
        title = soup.title

        if title and title.string:
            item["status"] = 1
            item["title"] = title.string.strip()
        else:
            item["status"] = 0
            item["title"] = ""

    except requests.exceptions.Timeout:
        print(f"TIMEOUT: {url}")
        item["status"] = 0
        item["title"] = ""

    except requests.exceptions.RequestException as e:
        print(f"REQUEST ERROR: {e}, URL: {url}")
        item["status"] = 0
        item["title"] = ""

    except Exception as e:
        print(f"PARSE ERROR: {e}, URL: {url}")
        item["status"] = 0
        item["title"] = ""

    finally:
        try:
            if "response" in locals():
                response.close()
        except Exception:
            pass
        time.sleep(0.2)



def fetch_titles(processed_posts, max_workers=15, min_delay=0.5):
    total_urls = sum(len(p.get("url_data", [])) for p in processed_posts)
    if total_urls == 0:
        print("No URLs found to process")
        return

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    progress = {"count": 0}
    lock = Lock()
    domain_lock = Lock()
    domain_next_available = {}
    tasks = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for post in processed_posts:
            for item in post.get("url_data", []):
                tasks.append(
                    executor.submit(
                        fetch_title_for_item,
                        item,
                        headers,
                        total_urls,
                        progress,
                        lock,
                        domain_lock,
                        domain_next_available,
                        min_delay
                    )
                )

        for future in as_completed(tasks):
            try:
                future.result()
            except Exception as exc:
                print(f"Unexpected error in title worker: {exc}")
