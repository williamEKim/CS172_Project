import lucene
import os, shutil, json
import time
from datetime import datetime, timezone
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, FieldType, LongPoint, IntPoint, StoredField  
from org.apache.lucene.index import IndexWriter, IndexWriterConfig, IndexOptions, DirectoryReader
from org.apache.lucene.store import NIOFSDirectory
from org.apache.lucene.search import IndexSearcher, BooleanClause, BooleanQuery, MatchAllDocsQuery
from org.apache.lucene.queryparser.classic import QueryParser, MultiFieldQueryParser


program_start = time.time()

def load_posts(data_dir):
    posts = []
    for filename in os.listdir(data_dir):
        if filename.endswith(".jsonl"):
            filepath = os.path.join(data_dir, filename)
            print(f"Loading {filepath}")

            with open(filepath, "r", encoding="utf-8") as file:
                for line in file:
                    try:
                        posts.append(json.loads(line))
                    except Exception as e:
                        print(f"Skipping line {e}")
    
    return posts


def parse_epoch(iso_str):
    if not iso_str:
        return 0
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except ValueError:
        return 0


def create_index(index_dir, posts):
    if not os.path.exists(index_dir):
        os.makedirs(index_dir)

    store = NIOFSDirectory(Paths.get(index_dir))
    analyzer = StandardAnalyzer()
    config = IndexWriterConfig(analyzer)
    config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
    writer = IndexWriter(store, config)

    meta_type = FieldType()
    meta_type.setStored(True)
    meta_type.setTokenized(False)

    text_type = FieldType()
    text_type.setStored(True)
    text_type.setTokenized(True)
    text_type.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)

    for post in posts:
        doc = Document()
        doc.add(Field("url", str(post.get("url") or ""), meta_type))
        doc.add(Field("author_did", str(post.get("author_did") or ""), meta_type))
        doc.add(Field("author_handle", str(post.get("author_handle") or ""), meta_type))
        doc.add(Field("author_display_name", str(post.get("author_display_name") or ""), text_type))
        doc.add(Field("created_at", str(post.get("created_at") or ""), meta_type))
        doc.add(Field("indexed_at", str(post.get("indexed_at") or ""), meta_type))
        doc.add(Field("text", str(post.get("text") or ""), text_type))

        for item in post.get("langs", []):
            doc.add(Field("langs", item, meta_type))

        doc.add(Field("like_count", str(post.get("like_count", 0)), meta_type))
        doc.add(Field("repost_count", str(post.get("repost_count", 0)), meta_type))
        doc.add(Field("reply_count", str(post.get("reply_count", 0)), meta_type))
        doc.add(Field("quote_count", str(post.get("quote_count", 0)), meta_type))
        doc.add(Field("is_reply", str(post.get("is_reply", False)), meta_type))
        doc.add(Field("reply_parent_uri", str(post.get("reply_parent_uri") or ""), meta_type))

        for item in post.get("url_data", []):
            if item.get("title"):
                doc.add(Field("link_title", str(item.get("title") or ""), text_type))
            doc.add(Field("link_url", str(item.get("url") or ""), meta_type))
            doc.add(Field("link_status", str(item.get("status", 0)), meta_type))

        # LongPoint indexes the value for range queries; StoredField lets us retrieve it later
        epoch = parse_epoch(post.get("created_at"))
        doc.add(LongPoint("created_at_epoch", epoch))
        doc.add(StoredField("created_at_epoch", epoch))

        # We keep the original string fields above for display; these are for numeric operations
        doc.add(IntPoint("like_count_int", int(post.get("like_count", 0))))
        doc.add(IntPoint("repost_count_int", int(post.get("repost_count", 0))))
        doc.add(IntPoint("reply_count_int", int(post.get("reply_count", 0))))
        doc.add(IntPoint("quote_count_int", int(post.get("quote_count", 0))))

        writer.addDocument(doc)

    writer.commit()
    writer.close()
    print(f"Indexed {len(posts)} documents to {index_dir}")
    

def search(store_dir, query):
    store = NIOFSDirectory(Paths.get(store_dir))
    reader = DirectoryReader.open(store)
    searcher = IndexSearcher(reader)

    parser = QueryParser("text", StandardAnalyzer())
    parsed_query = parser.parse(query)

    top_docs = searcher.search(parsed_query, 10).scoreDocs
    stored_fields = searcher.storedFields()
    top_k_docs = []

    for hit in top_docs:
        doc = stored_fields.document(hit.doc)
        top_k_docs.append({
            "score": hit.score,
            "url": doc.get("url"),
            "author_did": doc.get("author_did"),
            "author_handle": doc.get("author_handle"),
            "author_display_name": doc.get("author_display_name"),
            "created_at": doc.get("created_at"),
            "indexed_at": doc.get("indexed_at"),
            "text": doc.get("text"),
            "langs": list(doc.getValues("langs")),
            "like_count": doc.get("like_count"),
            "repost_count": doc.get("repost_count"),
            "reply_count": doc.get("reply_count"),
            "quote_count": doc.get("quote_count"),
            "is_reply": doc.get("is_reply"),
            "reply_parent_uri": doc.get("reply_parent_uri"),
            "title_list": list(doc.getValues("link_title")),
            "url_list": list(doc.getValues("link_url")),
            "status_list": list(doc.getValues("link_status")),
            "created_at_epoch": doc.get("created_at_epoch")
        })
    reader.close()
    top_k_docs = sorted(top_k_docs, key=lambda x: (x["score"], x["created_at_epoch"]), reverse=True)
    return top_k_docs


def multifield_search(index_dir, query):
    store = NIOFSDirectory(Paths.get(index_dir))
    reader = DirectoryReader.open(store)
    searcher = IndexSearcher(reader)

    fields = ["author_display_name", "text", "link_title"]
    SHOULD = BooleanClause.Occur.SHOULD
    parsed_query = MultiFieldQueryParser.parse(query, fields, [SHOULD, SHOULD, SHOULD], StandardAnalyzer())

    top_docs = searcher.search(parsed_query, 10).scoreDocs

    stored_fields = searcher.storedFields()
    top_k_docs = []
    for hit in top_docs:
        doc = stored_fields.document(hit.doc)
        top_k_docs.append({
            "score": hit.score,
            "url": doc.get("url"),
            "author_did": doc.get("author_did"),
            "author_handle": doc.get("author_handle"),
            "author_display_name": doc.get("author_display_name"),
            "created_at": doc.get("created_at"),
            "indexed_at": doc.get("indexed_at"),
            "text": doc.get("text"),
            "langs": list(doc.getValues("langs")),
            "like_count": doc.get("like_count"),
            "repost_count": doc.get("repost_count"),
            "reply_count": doc.get("reply_count"),
            "quote_count": doc.get("quote_count"),
            "is_reply": doc.get("is_reply"),
            "reply_parent_uri": doc.get("reply_parent_uri"),
            "title_list": list(doc.getValues("link_title")),
            "url_list": list(doc.getValues("link_url")),
            "status_list": list(doc.getValues("link_status")),
            "created_at_epoch": doc.get("created_at_epoch")
        })
    reader.close()
    top_k_docs = sorted(top_k_docs, key=lambda x: (x["score"], x["created_at_epoch"]), reverse=True)
    return top_k_docs


def advanced_search(index_dir, query_str, mode="multi", sort_by="score",
                    min_likes=0, min_reposts=0, date_from=None, date_to=None, limit=50):
    store = NIOFSDirectory(Paths.get(index_dir))
    reader = DirectoryReader.open(store)
    searcher = IndexSearcher(reader)

    MUST = BooleanClause.Occur.MUST
    FILTER = BooleanClause.Occur.FILTER
    builder = BooleanQuery.Builder()

    if query_str.strip():
        if mode == "multi":
            fields = ["author_display_name", "text", "link_title"]
            SHOULD = BooleanClause.Occur.SHOULD
            text_q = MultiFieldQueryParser.parse(
                query_str, fields, [SHOULD, SHOULD, SHOULD], StandardAnalyzer()
            )
        else:
            text_q = QueryParser("text", StandardAnalyzer()).parse(query_str)
        builder.add(text_q, MUST)
    else:
        builder.add(MatchAllDocsQuery(), MUST)

    if date_from or date_to:
        lo = parse_epoch(date_from + "T00:00:00Z") if date_from else 0
        hi = parse_epoch(date_to + "T23:59:59Z") if date_to else 9223372036854775807
        builder.add(LongPoint.newRangeQuery("created_at_epoch", lo, hi), FILTER)

    if min_likes > 0:
        builder.add(IntPoint.newRangeQuery("like_count_int", min_likes, 2147483647), FILTER)

    if min_reposts > 0:
        builder.add(IntPoint.newRangeQuery("repost_count_int", min_reposts, 2147483647), FILTER)

    top_docs = searcher.search(builder.build(), limit).scoreDocs

    stored_fields = searcher.storedFields()
    results = []
    for hit in top_docs:
        doc = stored_fields.document(hit.doc)
        results.append({
            "score": hit.score,
            "url": doc.get("url"),
            "author_did": doc.get("author_did"),
            "author_handle": doc.get("author_handle"),
            "author_display_name": doc.get("author_display_name"),
            "created_at": doc.get("created_at"),
            "indexed_at": doc.get("indexed_at"),
            "text": doc.get("text"),
            "langs": list(doc.getValues("langs")),
            "like_count": doc.get("like_count"),
            "repost_count": doc.get("repost_count"),
            "reply_count": doc.get("reply_count"),
            "quote_count": doc.get("quote_count"),
            "is_reply": doc.get("is_reply"),
            "reply_parent_uri": doc.get("reply_parent_uri"),
            "title_list": list(doc.getValues("link_title")),
            "url_list": list(doc.getValues("link_url")),
            "status_list": list(doc.getValues("link_status")),
            "created_at_epoch": doc.get("created_at_epoch"),
        })

    reader.close()

    if sort_by == "date":
        results.sort(key=lambda x: int(x["created_at_epoch"] or 0), reverse=True)
    elif sort_by == "likes":
        results.sort(key=lambda x: int(x["like_count"] or 0), reverse=True)
    elif sort_by == "reposts":
        results.sort(key=lambda x: int(x["repost_count"] or 0), reverse=True)
    else:
        results.sort(key=lambda x: (x["score"], int(x["created_at_epoch"] or 0)), reverse=True)

    return results


def show(results, query):
    print(f"\n   Query: {query!r}    ({len(results)} results)")
    print("-" * 78)
    for i, r in enumerate(results, 1):
        print(f"{i}.  Score: {r['score']:.5f}")
        print(f"URL: {r['url']}")
        print(f"Author DID: {r['author_did']}")
        print(f"Author Handle: {r['author_handle']}")
        print(f"Author Display Name: {r['author_display_name']}")
        print(f"Created At: {r['created_at']}")
        print(f"Indexed at: {r['indexed_at']}")
        print(f"Text: {r['text']}")
        print(f"Langs: {r['langs']}")
        print(f"Like Count: {r['like_count']}")
        print(f"Repost Count: {r['repost_count']}")
        print(f"Reply Count: {r['reply_count']}")
        print(f"Quote Count: {r['quote_count']}")
        print(f"Is Reply: {r['is_reply']}")
        print(f"Reply Parent URI: {r['reply_parent_uri']}")
        print(f"Title List: {r['title_list']}")
        print(f"URL List: {r['url_list']}")
        print(f"Status List: {r['status_list']}\n")


if __name__ == "__main__":
    lucene.initVM(vmargs=['-Djava.awt.headless=true'])
    INDEX_DIR = "bluesky_index"
    DATA_DIR = "processed"
    query = "volleyball tournament"

    if not os.path.exists(INDEX_DIR):
        load_start = time.time()
        posts = load_posts(DATA_DIR)
        print(f"Loaded {len(posts)} total posts")
        print(f"Loading took {time.time() - load_start:.2f} seconds")

        index_start = time.time()
        create_index(INDEX_DIR, posts)
        print(f"Indexing took {time.time() - index_start:.2f} seconds")
    else:
        print("Using existing index")

    search_start = time.time()
    results = search(INDEX_DIR, query)
    # results = multifield_search(INDEX_DIR, query)
    print(f"Search took {time.time() - search_start:.4f} seconds")

    show(results, query)
    print(f"Total runtime: {time.time() - program_start:.2f} seconds")