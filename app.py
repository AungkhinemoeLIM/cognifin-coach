"""CogniFin Coach - local demo server (standard library only).

Run:  python app.py            then open http://localhost:8000
Set GEMINI_API_KEY to use the Google AI Studio Gemini coach; otherwise the offline generator is used.
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cognifin.quiz import get_quiz           # noqa: E402
from cognifin.session import Session         # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
SESSIONS = {}


def load_dotenv(path):
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json", extra=None):
        data = body if isinstance(body, bytes) else (body if isinstance(body, str) else json.dumps(body)).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _json(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return {}

    def log_message(self, *a):  # quiet
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            with open(os.path.join(ROOT, "static", "index.html"), "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        if path == "/api/quiz":
            return self._send(200, {"items": get_quiz(),
                                    "llm_available": bool(os.environ.get("GEMINI_API_KEY")
                                                          or os.environ.get("GOOGLE_API_KEY"))})
        parts = path.strip("/").split("/")
        if (len(parts) == 4 and parts[:2] == ["api", "session"]
                and parts[3] in ("state", "export", "summary")):
            s = SESSIONS.get(parts[2])
            if not s:
                return self._send(404, {"error": "unknown session"})
            if parts[3] == "state":
                return self._send(200, s.state())
            if parts[3] == "summary":
                return self._send(200, s.summary())
            os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
            csv_text = s.to_csv()
            with open(os.path.join(ROOT, "logs", f"session_{s.id}.csv"), "w", newline="") as f:
                f.write(csv_text)
            return self._send(200, csv_text, "text/csv",
                              {"Content-Disposition": f"attachment; filename=session_{s.id}.csv"})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        path, body = self.path.split("?")[0], self._json()
        if path == "/api/start":
            seed = body.get("seed")
            seed = int(seed) if isinstance(seed, (int, str)) and str(seed).isdigit() else None
            s = Session(str(body.get("user_id") or "anon"), body.get("answers", {}),
                        coach_mode=body.get("coach_mode", "llm"), seed=seed,
                        plan=body.get("plan"))
            SESSIONS[s.id] = s
            return self._send(200, s.state())
        parts = path.strip("/").split("/")
        if len(parts) == 4 and parts[:2] == ["api", "session"]:
            s = SESSIONS.get(parts[2])
            if not s:
                return self._send(404, {"error": "unknown session"})
            try:
                if parts[3] == "step":
                    actions = body.get("actions", body.get("action", {}))
                    return self._send(200, s.step(actions, body.get("decision_ms"),
                                                   body.get("decision_reason"), body.get("confidence")))
                if parts[3] == "rate":
                    return self._send(200, {"ok": s.rate(int(body.get("turn", 0)), body.get("rating", 3))})
            except ValueError as e:
                return self._send(400, {"error": str(e)})
        self._send(404, {"error": "not found"})


if __name__ == "__main__":
    load_dotenv(os.path.join(ROOT, ".env"))
    port = int(os.environ.get("PORT", 8000))
    print(f"CogniFin Coach running at http://localhost:{port}  "
          f"(LLM: {'Google AI Studio' if os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY') else 'offline generator'})")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
