import asyncio
import hashlib
import json
import os
import random
import sqlite3
import time

import aiohttp

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 3128

DB_FILE = os.getenv("CACHE_DB", "cache.db")

CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"

#
# Example:
#
# DELAY_RULES='[
#   {
#     "contains":"brasilapi",
#     "delay":100,
#     "cached_delay":5000
#   },
#   {
#     "contains":"/cep/",
#     "delay":50,
#     "cached_delay":2000
#   }
# ]'
#
#
DELAY_RULES = json.loads(os.getenv("DELAY_RULES", "[]"))

conn = sqlite3.connect(DB_FILE, check_same_thread=False)

conn.execute("""
CREATE TABLE IF NOT EXISTS cache (
    cache_key TEXT PRIMARY KEY,
    url TEXT,
    method TEXT,
    status INTEGER,
    headers TEXT,
    body BLOB,
    created_at INTEGER
)
""")

conn.commit()


def build_cache_key(method: str, url: str) -> str:
    raw = f"{method}:{url}"
    return hashlib.sha256(raw.encode()).hexdigest()


def find_rule(url: str):
    for rule in DELAY_RULES:
        contains = rule.get("contains")

        if contains and contains in url:
            return rule

    return None


def calculate_delay(url: str, cached: bool = False) -> float:
    rule = find_rule(url)

    if not rule:
        return 0

    if cached:
        delay = float(rule.get("cached_delay", 0))
    else:
        delay = float(rule.get("delay", 0))

    jitter_min = float(rule.get("jitter_min", 0))
    jitter_max = float(rule.get("jitter_max", 0))

    if jitter_max > jitter_min:
        delay += random.uniform(jitter_min, jitter_max)

    return delay / 1000.0


async def apply_delay(url: str, cached: bool = False):
    delay = calculate_delay(url, cached)

    if delay > 0:
        if cached:
            print(f"[CACHE DELAY] {delay:.3f}s")
        else:
            print(f"[NETWORK DELAY] {delay:.3f}s")

        await asyncio.sleep(delay)


async def pipe(reader, writer):
    try:
        while True:
            data = await reader.read(8192)

            if not data:
                break

            writer.write(data)
            await writer.drain()

    except Exception:
        pass

    finally:
        try:
            writer.close()
        except Exception:
            pass


async def handle_connect(client_reader, client_writer, target):
    print(f"[CONNECT] {target}")

    await apply_delay(target)

    try:
        host, port = target.split(":")
        port = int(port)

        remote_reader, remote_writer = await asyncio.open_connection(
            host,
            port
        )

        client_writer.write(
            b"HTTP/1.1 200 Connection Established\r\n"
            b"Proxy-Agent: PythonProxy/1.0\r\n"
            b"\r\n"
        )

        await client_writer.drain()

        await asyncio.gather(
            pipe(client_reader, remote_writer),
            pipe(remote_reader, client_writer)
        )

    except Exception as e:
        print(f"[CONNECT ERROR] {e}")

        try:
            client_writer.write(
                b"HTTP/1.1 500 Connection Error\r\n\r\n"
            )

            await client_writer.drain()

        except Exception:
            pass

    finally:
        try:
            client_writer.close()
        except Exception:
            pass


async def send_cached_response(
    client_writer,
    status,
    headers_json,
    body_bytes
):
    response_headers = json.loads(headers_json)

    status_line = f"HTTP/1.1 {status} OK\r\n"

    client_writer.write(status_line.encode())

    for k, v in response_headers.items():
        header_line = f"{k}: {v}\r\n"
        client_writer.write(header_line.encode())

    client_writer.write(b"\r\n")
    client_writer.write(body_bytes)

    await client_writer.drain()


async def cache_response(
    cache_key,
    url,
    method,
    status,
    headers,
    body
):
    conn.execute("""
        INSERT OR REPLACE INTO cache (
            cache_key,
            url,
            method,
            status,
            headers,
            body,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        cache_key,
        url,
        method,
        status,
        json.dumps(headers),
        body,
        int(time.time())
    ))

    conn.commit()


async def handle_http(
    client_reader,
    client_writer,
    method,
    url,
    headers,
    body
):
    print(f"[HTTP] {method} {url}")

    cache_key = build_cache_key(method, url)

    #
    # CACHE HIT
    #
    if CACHE_ENABLED and method == "GET":

        cached = conn.execute(
            """
            SELECT
                status,
                headers,
                body
            FROM cache
            WHERE cache_key = ?
            """,
            (cache_key,)
        ).fetchone()

        if cached:
            print(f"[CACHE HIT] {url}")

            await apply_delay(url, cached=True)

            status, headers_json, body_bytes = cached

            await send_cached_response(
                client_writer,
                status,
                headers_json,
                body_bytes
            )

            client_writer.close()

            return

    #
    # NETWORK FETCH
    #
    await apply_delay(url, cached=False)

    headers.pop("Proxy-Connection", None)
    headers.pop("Connection", None)

    timeout = aiohttp.ClientTimeout(total=300)

    async with aiohttp.ClientSession(timeout=timeout) as session:

        async with session.request(
            method=method,
            url=url,
            headers=headers,
            data=body,
            ssl=False
        ) as resp:

            response_body = await resp.read()

            response_headers = dict(resp.headers)

            print(f"[FETCHED] {url} -> {resp.status}")

            #
            # CACHE STORE
            #
            if CACHE_ENABLED and method == "GET":

                await cache_response(
                    cache_key,
                    url,
                    method,
                    resp.status,
                    response_headers,
                    response_body
                )

            #
            # SEND RESPONSE
            #
            status_line = f"HTTP/1.1 {resp.status} OK\r\n"

            client_writer.write(status_line.encode())

            for k, v in response_headers.items():
                header_line = f"{k}: {v}\r\n"
                client_writer.write(header_line.encode())

            client_writer.write(b"\r\n")
            client_writer.write(response_body)

            await client_writer.drain()

    client_writer.close()


async def handle_client(client_reader, client_writer):

    client_addr = client_writer.get_extra_info("peername")

    try:

        request_line = await client_reader.readline()

        if not request_line:
            client_writer.close()
            return

        request_line = request_line.decode().strip()

        print(f"[REQUEST] {client_addr} -> {request_line}")

        parts = request_line.split()

        if len(parts) < 3:
            client_writer.close()
            return

        method, target, version = parts

        headers = {}

        while True:

            line = await client_reader.readline()

            if line in (b"\r\n", b"\n", b""):
                break

            decoded = line.decode().strip()

            if ":" in decoded:
                k, v = decoded.split(":", 1)
                headers[k.strip()] = v.strip()

        #
        # HTTPS TUNNEL
        #
        if method.upper() == "CONNECT":

            await handle_connect(
                client_reader,
                client_writer,
                target
            )

            return

        #
        # NORMAL HTTP REQUEST
        #
        content_length = int(headers.get("Content-Length", "0"))

        body = b""

        if content_length > 0:
            body = await client_reader.readexactly(content_length)

        await handle_http(
            client_reader,
            client_writer,
            method,
            target,
            headers,
            body
        )

    except Exception as e:

        print(f"[CLIENT ERROR] {e}")

        try:
            client_writer.write(
                b"HTTP/1.1 500 Internal Server Error\r\n\r\n"
            )

            await client_writer.drain()

        except Exception:
            pass

        try:
            client_writer.close()
        except Exception:
            pass


async def main():

    server = await asyncio.start_server(
        handle_client,
        LISTEN_HOST,
        LISTEN_PORT
    )

    print(f"v2 - Proxy listening on {LISTEN_HOST}:{LISTEN_PORT}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())