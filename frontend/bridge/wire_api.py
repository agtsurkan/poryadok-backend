#!/usr/bin/env python3
"""Wire a Claude Design standalone export to the Порядок backend.

The exported build persists to `localStorage['poryadok.data']`. This patcher
injects a small **bridge** script (before the bundler runs) that instead:

  * shows a login screen and exchanges email+password for a JWT;
  * hydrates the app from `GET /state` (by serving the server bundle to the
    app's `localStorage.getItem('poryadok.data')`);
  * mirrors every save (`setItem('poryadok.data', …)`) to `PUT /state`,
    debounced.

It is a *bridge* on the exported bundle, not a durable change to the design
source — but it is **reproducible**: re-run it on every new export.

    python frontend/wire_api.py <export.html> -o frontend/poryadok.html

Notes / known limits (by design, P0):
  * The build only persists tasks / inbox / events / events2 / quickLinks /
    services / links. projects/clients/directions aren't saved by this build
    (frontend bug, brief §11.1) — the backend keeps them safely (merge by
    presence), this build just doesn't display the server's copies yet. The
    durable fix lives in the design source.
  * Default API base is http://localhost:8000; editable on the login screen.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# The injected bridge. Vanilla JS, no deps. Must not contain the literal
# "</script>" sequence.
BRIDGE_JS = r"""
(function () {
  "use strict";
  // ── Порядок · API bridge (P0) ───────────────────────────────────────────
  var LS = window.localStorage;
  var realGet = LS.getItem.bind(LS);
  var realSet = LS.setItem.bind(LS);
  var realRemove = LS.removeItem.bind(LS);
  var DATA_KEY = "poryadok.data";
  var DEFAULT_API = "http://localhost:8000";

  function api() { return (realGet("poryadok.api") || DEFAULT_API).replace(/\/+$/, ""); }
  function token() { return realGet("poryadok.token"); }

  var serverData = null; // server bundle string, served to the app
  var putTimer = null;

  // Reads of poryadok.data come from the server once hydrated.
  LS.getItem = function (k) {
    return (k === DATA_KEY && serverData !== null) ? serverData : realGet(k);
  };
  // Writes of poryadok.data are mirrored to the server (debounced).
  LS.setItem = function (k, v) {
    realSet(k, v);
    if (k === DATA_KEY && token()) {
      serverData = v;
      clearTimeout(putTimer);
      putTimer = setTimeout(function () { putState(v); }, 700);
    }
  };

  function putState(body) {
    fetch(api() + "/state", {
      method: "PUT",
      headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token() },
      body: body
    }).then(function (r) { if (r.status === 401) logout(); })
      .catch(function () { /* offline — kept locally, resyncs on next save */ });
  }

  function logout() { realRemove("poryadok.token"); location.reload(); }

  // Synchronous hydration, so componentDidMount sees server data.
  function hydrate() {
    if (!token()) return "anon";
    try {
      var x = new XMLHttpRequest();
      x.open("GET", api() + "/state", false);
      x.setRequestHeader("Authorization", "Bearer " + token());
      x.send(null);
      if (x.status === 200) { serverData = x.responseText; return "ok"; }
      if (x.status === 401) { realRemove("poryadok.token"); return "anon"; }
      return "error";
    } catch (e) { return "offline"; }
  }

  function loginHTML(apiUrl, message) {
    return ""
      + "<style>"
      + "#poryadok-login{position:fixed;inset:0;z-index:2147483647;display:flex;align-items:center;"
      + "justify-content:center;background:#E9E4D9;font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text',sans-serif;color:#26221C}"
      + "#poryadok-login .card{width:340px;max-width:88vw;background:#FFFCF6;border:1px solid #E7DECB;"
      + "border-radius:18px;padding:28px 26px;box-shadow:0 8px 30px rgba(38,34,28,.10)}"
      + "#poryadok-login h1{font-size:21px;font-weight:600;margin:0 0 4px}"
      + "#poryadok-login p.sub{font-size:13px;color:#6B6457;margin:0 0 18px}"
      + "#poryadok-login label{display:block;font-size:12px;color:#6B6457;margin:14px 0 6px}"
      + "#poryadok-login input{width:100%;padding:11px 13px;border:1px solid #E7DECB;border-radius:11px;"
      + "background:#fff;font-size:15px;color:#26221C;outline:none}"
      + "#poryadok-login input:focus{border-color:#B5763A}"
      + "#poryadok-login button{width:100%;margin-top:20px;padding:12px;border:0;border-radius:11px;"
      + "background:#B5763A;color:#fff;font-size:15px;font-weight:600;cursor:pointer}"
      + "#poryadok-login button:disabled{opacity:.6;cursor:default}"
      + "#poryadok-login .err{color:#B0492F;font-size:13px;min-height:18px;margin-top:10px}"
      + "#poryadok-login details{margin-top:14px}#poryadok-login summary{font-size:12px;color:#9C9483;cursor:pointer}"
      + "</style>"
      + "<form id='pl-form' class='card'>"
      + "<h1>Порядок</h1><p class='sub'>Войдите, чтобы продолжить</p>"
      + "<label>Email</label><input id='pl-email' type='email' autocomplete='username' value='demo@poryadok.app' required>"
      + "<label>Пароль</label><input id='pl-pass' type='password' autocomplete='current-password' required>"
      + "<button id='pl-btn' type='submit'>Войти</button>"
      + "<div class='err' id='pl-err'>" + (message || "") + "</div>"
      + "<details><summary>Сервер</summary><label>Адрес API</label>"
      + "<input id='pl-api' type='text' value='" + apiUrl + "'></details>"
      + "</form>";
  }

  function showLogin(message) {
    function build() {
      if (document.getElementById("poryadok-login")) return;
      var wrap = document.createElement("div");
      wrap.id = "poryadok-login";
      wrap.innerHTML = loginHTML(api(), message);
      document.body.appendChild(wrap);
      document.getElementById("pl-form").addEventListener("submit", function (e) {
        e.preventDefault();
        var err = document.getElementById("pl-err");
        var btn = document.getElementById("pl-btn");
        var base = (document.getElementById("pl-api").value.trim() || DEFAULT_API).replace(/\/+$/, "");
        var email = document.getElementById("pl-email").value.trim();
        var pass = document.getElementById("pl-pass").value;
        err.textContent = ""; btn.disabled = true; btn.textContent = "Вход…";
        fetch(base + "/auth/login", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: email, password: pass })
        }).then(function (r) {
          return r.ok ? r.json() : r.json().then(function (j) { throw new Error(j.detail || "Не вышло войти"); });
        }).then(function (j) {
          realSet("poryadok.api", base);
          realSet("poryadok.token", j.access_token || j.token);
          location.reload();
        }).catch(function (ex) {
          err.textContent = (ex && ex.message) ? ex.message : "Сервер недоступен";
          btn.disabled = false; btn.textContent = "Войти";
        });
      });
    }
    if (document.body) build();
    else document.addEventListener("DOMContentLoaded", build);
  }

  var state = hydrate(); // runs in <head>, before the app boots
  if (state === "anon") showLogin("");
  else if (state === "offline") showLogin("Сервер недоступен — проверь адрес.");
  else if (state === "error") showLogin("Ошибка сервера. Войдите заново.");
  // state === "ok": app boots with server data, no overlay.
})();
"""


def wire(html: str) -> str:
    if "poryadok-api-bridge" in html:
        raise SystemExit("This file already has the API bridge injected.")
    if "<head>" not in html:
        raise SystemExit("No <head> found — is this a Claude Design export?")
    bridge = '<script id="poryadok-api-bridge">' + BRIDGE_JS + "</script>\n"
    # Inject before anything else in <head>, so it patches localStorage first.
    html = html.replace("<head>", "<head>\n" + bridge, 1)
    html = html.replace("<title>Bundled Page</title>", "<title>Порядок</title>", 1)
    return html


def main() -> None:
    ap = argparse.ArgumentParser(description="Wire a Claude Design export to the Порядок API.")
    ap.add_argument("source", type=Path, help="exported standalone .html")
    ap.add_argument("-o", "--output", type=Path, default=Path("frontend/poryadok.html"))
    args = ap.parse_args()

    if not args.source.exists():
        sys.exit(f"not found: {args.source}")
    out = wire(args.source.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(out, encoding="utf-8")
    print(f"wired → {args.output}  ({len(out):,} bytes)")


if __name__ == "__main__":
    main()
