import http.server
import socketserver
import urllib.parse
import sys

# --- Read port from command-line args ---
# Usage: python WebPaste.py [PORT]
DEFAULT_PORT = 8000
PORT = DEFAULT_PORT

if len(sys.argv) > 1:
    try:
        PORT = int(sys.argv[1])
        if not (1 <= PORT <= 65535):
            raise ValueError
    except ValueError:
        print(f"Invalid port: {sys.argv[1]!r}. Using default port {DEFAULT_PORT}.")
        PORT = DEFAULT_PORT

# The latest submitted text is kept in memory
latest_text = {"content": ""}

# HTML page template
PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shared Text</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 20px auto;
            padding: 15px;
            background: #f5f5f5;
        }}
        h1 {{ font-size: 1.4em; }}
        textarea {{
            width: 100%;
            height: 100px;
            padding: 10px;
            font-size: 1em;
            box-sizing: border-box;
            border-radius: 8px;
            border: 1px solid #ccc;
        }}
        button {{
            margin-top: 10px;
            padding: 12px 24px;
            font-size: 1em;
            background: #2c7be5;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }}
        button:active {{ background: #1a5bb8; }}
        .latest-box {{
            margin-top: 15px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            border: 1px solid #ddd;
            white-space: pre-wrap;
            word-break: break-word;
            min-height: 60px;
        }}
        #copyBtn {{ background: #28a745; display: none; }}
    </style>
</head>
<body>
    <h1>Latest Submitted Text</h1>
    <div class="latest-box" id="latestBox">{latest}</div>
    <button id="copyBtn" onclick="copyLatest()">Copy Text</button>

    <hr style="margin: 25px 0;">

    <h2 style="font-size: 1.1em;">Submit New Text</h2>
    <form method="POST" action="/">
        <textarea name="text" placeholder="Write your text here..." required></textarea>
        <button type="submit">Submit</button>
    </form>

    <script>
        const latestText = document.getElementById("latestBox").innerText.trim();
        if (latestText && latestText !== "No text has been submitted yet.") {{
            document.getElementById("copyBtn").style.display = "inline-block";
        }}

        function copyLatest() {{
            const text = document.getElementById("latestBox").innerText;
            navigator.clipboard.writeText(text).then(() => {{
                const btn = document.getElementById("copyBtn");
                btn.textContent = "Copied ✓";
                setTimeout(() => btn.textContent = "Copy Text", 1500);
            }});
        }}

        // Auto-refresh every 3 seconds (skip if the user is typing)
        setInterval(() => {{
            const ta = document.querySelector("textarea");
            if (document.activeElement !== ta || ta.value === "") {{
                location.reload();
            }}
        }}, 3000);
    </script>
</body>
</html>
"""


def escape_html(text):
    """Prevent HTML injection"""
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))


class Handler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_page()

    def do_POST(self):
        global latest_text
        # Read the request body
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        params = urllib.parse.parse_qs(body)
        text = params.get("text", [""])[0].strip()
        if text:
            latest_text["content"] = text
        # Redirect back to the main page after submitting
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

    def send_page(self):
        content = latest_text["content"]
        display = escape_html(content) if content else "No text has been submitted yet."
        html = PAGE_TEMPLATE.format(latest=display).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)

    def log_message(self, format, *args):
        # Silence default request logs (optional)
        pass


# allow_reuse_address prevents "Address already in use" errors
socketserver.TCPServer.allow_reuse_address = True

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"Server running on port {PORT}...")
    print(f"From other devices on the LAN: http://<YOUR-IP>:{PORT}")
    httpd.serve_forever()
