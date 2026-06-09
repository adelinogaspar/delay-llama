import hashlib
import json
import os
import sqlite3
import time

from mitmproxy import http

DB_FILE = os.getenv("CACHE_DB", "/data/cache.db")

DELAY_MS = int(os.getenv("CACHED_DELAY_MS", "5000"))

conn = sqlite3.connect(DB_FILE, check_same_thread=False)

conn.execute("""
CREATE TABLE IF NOT EXISTS cache (
    cache_key TEXT PRIMARY KEY,
    method TEXT,
    url TEXT,
    request_body BLOB,
    status INTEGER,
    headers TEXT,
    body BLOB,
    created_at INTEGER
)
""")

conn.commit()


def cache_key(flow: http.HTTPFlow):

    request_body = flow.request.raw_content or b""

    raw = (
        flow.request.method
        + "|"
        + flow.request.pretty_url
        + "|"
        + request_body.decode(errors="ignore")
    )

    return hashlib.sha256(raw.encode()).hexdigest()


def response(flow: http.HTTPFlow):

    key = cache_key(flow)

    response_body = flow.response.content

    response_headers = dict(flow.response.headers)

    request_body = flow.request.raw_content or b""

    conn.execute("""
        INSERT OR REPLACE INTO cache (
            cache_key,
            method,
            url,
            request_body,
            status,
            headers,
            body,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        key,
        flow.request.method,
        flow.request.pretty_url,
        request_body,
        flow.response.status_code,
        json.dumps(response_headers),
        response_body,
        int(time.time())
    ))

    conn.commit()

    print(
        f"[CACHED] "
        f"{flow.request.method} "
        f"{flow.request.pretty_url}"
    )


def request(flow: http.HTTPFlow):

    key = cache_key(flow)

    cached = conn.execute("""
        SELECT
            status,
            headers,
            body
        FROM cache
        WHERE cache_key = ?
    """, (key,)).fetchone()

    if not cached:
        print(
            f"[CACHE MISS] "
            f"{flow.request.method} "
            f"{flow.request.pretty_url}"
        )
        return

    print(
        f"[CACHE HIT] "
        f"{flow.request.method} "
        f"{flow.request.pretty_url}"
    )

    time.sleep(DELAY_MS / 1000)

    status, headers_json, body = cached

    headers = json.loads(headers_json)

    flow.response = http.Response.make(
        status,
        body,
        headers
    )