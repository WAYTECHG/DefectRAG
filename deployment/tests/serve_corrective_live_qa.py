"""Loopback-only console; serves installed public SDK/config, never secrets/.env.
No packages installed; no production activation or background test execution.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_CONFIG = Path("C:/Users/User/Desktop/DefectRAG-v2/frontend/public/config.js")
FILES = {
    "/": (Path(__file__).with_name("corrective_live_qa.html"), "text/html"),
    "/qa.mjs": (Path(__file__).with_name("corrective_live_qa.mjs"), "text/javascript"),
    "/sink-approval": (Path(__file__).with_name("corrective_sink_approval.html"), "text/html"),
    "/sink-approval.mjs": (Path(__file__).with_name("corrective_sink_approval.mjs"), "text/javascript"),
    "/sink-lifecycle.mjs": (Path(__file__).with_name("corrective_sink_lifecycle.mjs"), "text/javascript"),
    "/config.js": (PUBLIC_CONFIG, "text/javascript"),
    "/sdk.js": (ROOT / "frontend/node_modules/@supabase/supabase-js/dist/umd/supabase.js", "text/javascript"),
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.headers.get("Host") not in ("127.0.0.1:5198", "localhost:5198"):
            self.send_error(403)
            return
        target = FILES.get(self.path.split("?", 1)[0])
        if not target:
            self.send_error(404)
            return
        data = target[0].read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", target[1] + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' https://zrzqpbcomlorfzszolrs.supabase.co; img-src 'self' data: blob:; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    print("Live QA console: http://127.0.0.1:5198 (public client only; no automatic writes)", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 5198), Handler).serve_forever()
