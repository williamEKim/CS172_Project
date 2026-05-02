import requests
import time
import json, os
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse

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


_url_count = 0
def fetch_titles(processed_posts):
    global _url_count

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for post in processed_posts:
        url_data = post.get("url_data", [])
        
        if url_data:
            for item in url_data:
                try:
                    url = item["url"]

                    if not url: # empty url list
                        continue

                    if "bit.ly" in url: # short links
                        print("Skipping bit.ly links")
                        continue

                    try:
                        with requests.get(url, timeout=(3, 5), headers=headers) as page:

                            if page.status_code != 200:
                                item["status"] = 0
                                item["title"] = ""
                                continue

                            content_type = page.headers.get("Content-Type", "")

                            if "text/html" not in content_type:
                                item["status"] = 0
                                item["title"] = ""
                                continue

                            soup = BeautifulSoup(page.content, "html.parser")
                            title = soup.title
                            
                            if title and title.string:
                                item["status"] = 1
                                item["title"] = title.string
                                # _url_count += 1
                                # print(f"Successful URL Count: {_url_count}")
                            else:
                                # no title for page
                                item["status"] = 0
                                item["title"] = ""
                        
                        time.sleep(0.2)

                    except requests.exceptions.Timeout:
                        item["status"] = 0
                        item["title"] = ""
                        print(f"Timeout: {url}")
                        continue

                    except requests.exceptions.RequestException as e:
                        item["status"] = 0
                        item["title"] = ""
                        print(f"Request Error: {e}, URL: {url}")
                        continue

                    except Exception as e:
                        item["status"] = 0
                        item["title"] = ""
                        print(f"Parsing Error: {e}, URL: {url}")
                        continue
                    
                except Exception as e:
                    item["status"] = 0
                    item["title"] = ""
                    print(f"Error: {e}")
                    continue




    