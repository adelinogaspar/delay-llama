FROM mitmproxy/mitmproxy

COPY mitm_addon.py /addons/mitm_addon.py

CMD ["mitmdump", "--listen-host", "0.0.0.0", "--listen-port", "3120", "-s", "/addons/mitm_addon.py", "--ssl-insecure"]