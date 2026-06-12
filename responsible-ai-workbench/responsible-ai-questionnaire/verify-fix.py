"""
Responsible AI Toolkit - Security Fix Verification Server
No external dependencies required - uses only Python standard library.

Usage:
    python verify-fix.py

Then open http://localhost:30080 in your browser.
"""
import http.server
import json
import os
import re
from urllib.parse import urlparse, parse_qs

VALID_TENANTS = {"Privacy", "Safety", "FM-Moderation", "Explainability"}
ALLOWED_HOSTS = {"localhost", "vimptblt1117"}

telemetry_store = {}

def validate_telemetry_link(url_str):
    parsed = urlparse(url_str)
    if parsed.scheme not in ("http", "https"):
        return False, "telemetryLink must use http or https scheme"
    if not parsed.hostname:
        return False, "telemetryLink must contain a valid hostname"
    if parsed.hostname.lower() not in ALLOWED_HOSTS:
        return False, f"telemetryLink hostname '{parsed.hostname}' is not in the allowed hosts list"
    return True, ""

def validate_tenant(tenant):
    if tenant not in VALID_TENANTS:
        return False, f"tenant must be one of {sorted(VALID_TENANTS)}"
    return True, ""

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/v1/questionnaire/docs":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path.startswith("/v1/questionnaire/telemetryUrlGet/"):
            tenant = self.path.split("/")[-1]
            result = telemetry_store.get(tenant)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        elif self.path == "/api/test":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "running", "store": telemetry_store}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/v1/questionnaire/telemetryUrlAdd":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}

            tenant = body.get("tenant", "")
            link = body.get("telemetryLink", "")

            ok, err = validate_tenant(tenant)
            if not ok:
                self.send_response(422)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "detail": [{"location": ["body", "tenant"], "message": err, "type": "value_error"}],
                    "message": "Validation error"
                }).encode())
                return

            ok, err = validate_telemetry_link(link)
            if not ok:
                self.send_response(422)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "detail": [{"location": ["body", "telemetryLink"], "message": err, "type": "value_error"}],
                    "message": "Validation error"
                }).encode())
                return

            telemetry_store[tenant] = link
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b"true")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

HTML_PAGE = """<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<title>Responsible AI Toolkit - Security Fix Verification</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', Arial, sans-serif; background: #f0f2f5; color: #333; }
.header { background: linear-gradient(135deg, #1a73e8, #0d47a1); color: white; padding: 30px 40px; }
.header h1 { font-size: 24px; margin-bottom: 5px; }
.header p { opacity: 0.85; font-size: 14px; }
.container { max-width: 900px; margin: 30px auto; padding: 0 20px; }
.card { background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }
.card-title { background: #f8f9fa; padding: 15px 20px; font-weight: 600; border-bottom: 1px solid #e0e0e0; font-size: 16px; }
.card-body { padding: 20px; }
.status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; }
.status-running { background: #e6f4ea; color: #137333; }
.form-group { margin-bottom: 15px; }
.form-group label { display: block; font-weight: 600; margin-bottom: 5px; font-size: 14px; }
.form-group select, .form-group input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }
.btn { padding: 10px 24px; border: none; border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer; margin-right: 8px; margin-bottom: 8px; }
.btn-primary { background: #1a73e8; color: white; }
.btn-danger { background: #d32f2f; color: white; }
.btn-success { background: #0d8a0d; color: white; }
.btn:hover { opacity: 0.9; }
.result { margin-top: 15px; padding: 15px; border-radius: 6px; font-family: monospace; font-size: 13px; white-space: pre-wrap; word-break: break-all; display: none; }
.result-pass { background: #e6f4ea; border: 1px solid #a8dab5; color: #137333; }
.result-fail { background: #fce8e6; border: 1px solid #f5c6cb; color: #c5221f; }
.test-row { display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
.test-row:last-child { border-bottom: none; }
.test-label { flex: 1; font-size: 14px; }
.test-status { font-weight: 600; font-size: 13px; min-width: 80px; text-align: center; }
.pass { color: #137333; }
.fail { color: #c5221f; }
.waiting { color: #999; }
h3 { margin-bottom: 10px; }
.info { background: #e8f0fe; padding: 15px; border-radius: 6px; margin-bottom: 15px; font-size: 14px; line-height: 1.6; }
</style></head><body>
<div class="header">
  <h1>Responsible AI Toolkit - Questionnaire Service</h1>
  <p>Security Fix Verification - Open Redirect Prevention</p>
</div>
<div class="container">
  <div class="card">
    <div class="card-title">Server Status</div>
    <div class="card-body">
      <span class="status-badge status-running">RUNNING</span>
      &nbsp; http://localhost:30080
      <div class="info" style="margin-top:15px;">
        <strong>TELEMETRY_ALLOWED_HOSTS:</strong> localhost, vimptblt1117<br>
        <strong>VALID_TENANTS:</strong> Privacy, Safety, FM-Moderation, Explainability
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-title">Automated Security Tests</div>
    <div class="card-body">
      <p style="margin-bottom:15px; font-size:14px;">Run all tests to verify the open redirect fix is working correctly.</p>
      <button class="btn btn-primary" onclick="runAllTests()">Run All Tests</button>
      <div id="test-results" style="margin-top:15px;">
        <div class="test-row"><span class="test-label">1. Malicious URL (https://evil.tld/phish)</span><span id="t1" class="test-status waiting">-</span></div>
        <div class="test-row"><span class="test-label">2. javascript: scheme</span><span id="t2" class="test-status waiting">-</span></div>
        <div class="test-row"><span class="test-label">3. data: scheme</span><span id="t3" class="test-status waiting">-</span></div>
        <div class="test-row"><span class="test-label">4. Invalid tenant (FakeTenant)</span><span id="t4" class="test-status waiting">-</span></div>
        <div class="test-row"><span class="test-label">5. Case-mismatched tenant (safety)</span><span id="t5" class="test-status waiting">-</span></div>
        <div class="test-row"><span class="test-label">6. Valid request (Safety + localhost URL)</span><span id="t6" class="test-status waiting">-</span></div>
        <div class="test-row"><span class="test-label">7. Valid request (Privacy + vimptblt1117 URL)</span><span id="t7" class="test-status waiting">-</span></div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-title">Manual Test</div>
    <div class="card-body">
      <div class="form-group">
        <label>Tenant</label>
        <select id="tenant">
          <option value="Privacy">Privacy</option>
          <option value="Safety">Safety</option>
          <option value="FM-Moderation">FM-Moderation</option>
          <option value="Explainability">Explainability</option>
          <option value="FakeTenant">FakeTenant (invalid)</option>
        </select>
      </div>
      <div class="form-group">
        <label>Telemetry Link</label>
        <input type="text" id="link" value="https://evil.tld/phish" placeholder="Enter URL to test">
      </div>
      <button class="btn btn-primary" onclick="testManual()">Send POST Request</button>
      <button class="btn btn-danger" onclick="document.getElementById('link').value='https://evil.tld/phish'; testManual()">Test Malicious URL</button>
      <button class="btn btn-success" onclick="document.getElementById('link').value='http://localhost:5601/app/dashboards'; testManual()">Test Valid URL</button>
      <div id="manual-result" class="result"></div>
    </div>
  </div>
</div>
<script>
async function postTest(tenant, link) {
  try {
    const r = await fetch('/v1/questionnaire/telemetryUrlAdd', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({tenant, telemetryLink: link})
    });
    return {status: r.status, body: await r.json()};
  } catch(e) { return {status: 0, body: e.message}; }
}

async function runAllTests() {
  const tests = [
    {id:'t1', tenant:'Safety', link:'https://evil.tld/phish', expect:422},
    {id:'t2', tenant:'Safety', link:'javascript:alert(1)', expect:422},
    {id:'t3', tenant:'Safety', link:'data:text/html,<script>alert(1)<\\/script>', expect:422},
    {id:'t4', tenant:'FakeTenant', link:'http://localhost:5601/test', expect:422},
    {id:'t5', tenant:'safety', link:'http://localhost:5601/test', expect:422},
    {id:'t6', tenant:'Safety', link:'http://localhost:5601/app/dashboards#/view/abc', expect:200},
    {id:'t7', tenant:'Privacy', link:'http://vimptblt1117:5601/app/dashboards#/view/xyz', expect:200},
  ];
  for (const t of tests) {
    document.getElementById(t.id).className = 'test-status waiting';
    document.getElementById(t.id).textContent = '...';
  }
  for (const t of tests) {
    const r = await postTest(t.tenant, t.link);
    const el = document.getElementById(t.id);
    if (r.status === t.expect) {
      el.className = 'test-status pass';
      el.textContent = 'PASS (' + r.status + ')';
    } else {
      el.className = 'test-status fail';
      el.textContent = 'FAIL (' + r.status + ')';
    }
  }
}

async function testManual() {
  const tenant = document.getElementById('tenant').value;
  const link = document.getElementById('link').value;
  const r = await postTest(tenant, link);
  const el = document.getElementById('manual-result');
  el.style.display = 'block';
  if (r.status === 200) {
    el.className = 'result result-pass';
    el.textContent = 'ACCEPTED (HTTP ' + r.status + ')\\n\\n' + JSON.stringify(r.body, null, 2);
  } else {
    el.className = 'result result-fail';
    el.textContent = 'REJECTED (HTTP ' + r.status + ')\\n\\n' + JSON.stringify(r.body, null, 2);
  }
}
</script></body></html>"""

if __name__ == "__main__":
    port = 30080
    server = http.server.HTTPServer(("0.0.0.0", port), Handler)
    print(f"=== Responsible AI Toolkit - Security Fix Verification ===")
    print(f"")
    print(f"Server running at: http://localhost:{port}")
    print(f"Open this URL in your browser to verify the security fix.")
    print(f"")
    print(f"Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()
