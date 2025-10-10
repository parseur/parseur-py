from datetime import datetime
import logging
import subprocess
import sys
import threading

import requests

# Port for the local Flask server
LOCAL_PORT = 31313

try:
    from flask import Flask, request
except ImportError as e:
    raise ImportError(
        "The 'listen' feature requires Flask. "
        "Please install with: pip install parseur-py[listener]"
    ) from e
import parseur


def start_flask(app):
    """Run Flask silently (no dev warning, no werkzeug logs)."""
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)

    app.env = "production"
    app.debug = False
    app.run(port=LOCAL_PORT, use_reloader=False)


def start_localtunnel():
    """Start localtunnel via npx and parse 'your url is:' output."""
    lt_process = subprocess.Popen(
        ["npx", "--yes", "localtunnel", "--port", str(LOCAL_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    public_url = None
    while True:
        line = lt_process.stdout.readline()
        if not line:
            break

        line = line.strip().lower()
        if line.startswith("your url is:"):
            public_url = line.split(":", 1)[1].strip()
            break

    if not public_url:
        print("❌ Could not retrieve public URL from localtunnel", file=sys.stderr)
        lt_process.terminate()
        sys.exit(1)

    return public_url, lt_process


def check_localtunnel():
    """Verify that `npx` and `localtunnel` are installed."""
    try:
        subprocess.run(
            ["npx", "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ 'npx' not found. Please install Node.js:", file=sys.stderr)
        sys.exit(1)

    try:
        subprocess.run(
            ["npx", "--yes", "localtunnel", "--help"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ 'localtunnel' is not installed globally.", file=sys.stderr)
        print("   Install it with: npm install -g localtunnel", file=sys.stderr)
        sys.exit(1)


def create_app(redirect_url=None, silent=False):
    """
    Create and configure a Flask app that:
    - Logs incoming webhook events
    - Optionally forwards them to redirect_url
    """
    app = Flask(__name__)

    @app.route("/", methods=["POST"])
    def webhook():
        data = request.json
        if not redirect_url or not silent:
            print(f"📩 Event received at {datetime.now().isoformat()}")
        if not silent:
            print(parseur.to_json(data))

        if redirect_url:
            try:
                f_headers = dict(request.headers)
                resp = requests.post(
                    redirect_url, json=data, headers=f_headers, timeout=10
                )
                print(f"➡️ Forwarded to {redirect_url}, response {resp.status_code}")
            except Exception as e:
                print(f"⚠️ Failed to forward to {redirect_url}: {e}")

        return {"status": "ok"}, 200

    return app


def run_listener(
    event,
    mailbox_id,
    table_field_id,
    headers,
    name,
    redirect_url=None,
    silent=False,
):
    """
    - Check localtunnel installation
    - Start Flask server
    - Start localtunnel and get public URL
    - Create webhook in Parseur with provided options
    - Print and forward live events
    """

    # 0. Verify npx/localtunnel installation
    check_localtunnel()

    # 1. Build Flask app with closure capturing redirect_url
    app = create_app(redirect_url, silent)

    # 2. Start Flask in background thread
    print(f"🚀 Starting Flask server on port {LOCAL_PORT}...")
    flask_thread = threading.Thread(target=lambda: start_flask(app), daemon=True)
    flask_thread.start()

    # 3. Start localtunnel
    print(f'🔗 Starting localtunnel via "npx localtunnel --port {LOCAL_PORT}"...')
    public_url, lt_process = start_localtunnel()
    print(f"🌍 Public URL: {public_url}")

    # 4. Register webhook
    result = parseur.Webhook.create(
        event=event,
        target_url=public_url,
        mailbox_id=mailbox_id,
        table_field_id=table_field_id,
        headers=headers or None,
        name=name,
    )
    webhook_id = result.get("id")
    print(
        f"✅ Webhook {webhook_id} registered for event '{event}' "
        f"(mailbox={mailbox_id}, table_field_id={table_field_id})"
    )
    print("🔄 Listening for incoming events...")

    try:
        lt_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping listener...")
        lt_process.terminate()
        parseur.Webhook.delete(webhook_id)
        print(f"🗑️  Webhook {webhook_id} deleted.")
