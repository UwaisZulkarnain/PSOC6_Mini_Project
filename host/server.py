import time
import json
import threading
from flask import Flask, send_from_directory, jsonify
from flask_sock import Sock

app = Flask(__name__, static_folder=None)
sock = Sock(app)

clients = set()
clients_lock = threading.Lock()
hit_counts = {name: 0 for name in ["kick", "snare", "hihat_closed", "hihat_open", "crash", "tom", "ride"]}
hit_counts_lock = threading.Lock()
start_time = time.time()


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/stats")
def stats():
    with hit_counts_lock:
        counts = dict(hit_counts)
        total = sum(counts.values())
    uptime = time.time() - start_time
    return jsonify({"counts": counts, "total": total, "uptime_s": round(uptime, 1)})


@sock.route("/ws")
def ws(ws):
    with clients_lock:
        clients.add(ws)
    try:
        while True:
            ws.receive(timeout=30)
    except:
        pass
    finally:
        with clients_lock:
            clients.discard(ws)


def broadcast_hit(index, name):
    payload = json.dumps({"pad": name, "index": index, "ts": int(time.time() * 1000)})
    dead = []
    with clients_lock:
        for ws in clients:
            try:
                ws.send(payload)
            except:
                dead.append(ws)
        for ws in dead:
            clients.discard(ws)
    with hit_counts_lock:
        hit_counts[name] += 1


def run_server(host="0.0.0.0", port=5000):
    app.run(host=host, port=port, debug=False, use_reloader=False)