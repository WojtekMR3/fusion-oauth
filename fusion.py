#!/usr/bin/env python3
"""fusion-oauth — prompt multiple models of your choice in parallel, then judge.

Credentials are read at RUNTIME and NEVER written to disk or committed:
  - claude-oauth   : ~/.claude/.credentials.json  (your Claude Code login)
  - minimax-oauth  : ~/.hermes/auth.json          (your MiniMax OAuth login)
  - api-key        : an environment variable you name in providers.yaml

Usage:
  python3 fusion.py "your prompt"
  echo "your prompt" | python3 fusion.py
  python3 fusion.py --config providers.yaml "your prompt"
"""
import os, sys, json, time, urllib.request, urllib.error, concurrent.futures

try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")

HOME = os.path.expanduser("~")
CLAUDE_CREDS = os.path.join(HOME, ".claude", ".credentials.json")
MINIMAX_AUTH = os.path.join(HOME, ".hermes", "auth.json")


def _post(url, headers, body):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), method="POST",
        headers={**headers, "Content-Type": "application/json"})
    t0 = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=120)
        return json.load(r), round(time.time() - t0, 1), None
    except urllib.error.HTTPError as e:
        return None, round(time.time() - t0, 1), f"HTTP {e.code}: {e.read().decode()[:300]}"
    except Exception as e:
        return None, round(time.time() - t0, 1), f"{type(e).__name__}: {e}"


def _anthropic_text(d):
    return "".join(b.get("text", "") for b in d.get("content", []))


def call_claude_oauth(p, prompt, max_tokens):
    creds = json.load(open(CLAUDE_CREDS))["claudeAiOauth"]
    body = {"model": p["model"], "max_tokens": max_tokens,
            "system": "You are Claude Code, Anthropic's official CLI for Claude.",
            "messages": [{"role": "user", "content": prompt}]}
    headers = {"Authorization": f"Bearer {creds['accessToken']}",
               "anthropic-version": "2023-06-01",
               "anthropic-beta": "oauth-2025-04-20"}
    d, secs, err = _post("https://api.anthropic.com/v1/messages", headers, body)
    return (_anthropic_text(d) if d else None), secs, err


def call_minimax_oauth(p, prompt, max_tokens):
    mm = json.load(open(MINIMAX_AUTH))["providers"]["minimax-oauth"]
    body = {"model": p["model"], "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]}
    headers = {"Authorization": f"Bearer {mm['access_token']}",
               "anthropic-version": "2023-06-01"}
    d, secs, err = _post(mm["inference_base_url"] + "/v1/messages", headers, body)
    return (_anthropic_text(d) if d else None), secs, err


def call_api_key(p, prompt, max_tokens):
    key = os.environ.get(p["api_key_env"])
    if not key:
        return None, 0.0, f"env var {p['api_key_env']} not set"
    body = {"model": p["model"], "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]}
    headers = {"Authorization": f"Bearer {key}"}
    d, secs, err = _post(p["endpoint"], headers, body)
    if not d:
        return None, secs, err
    # OpenAI-style or Anthropic-style response
    if "choices" in d:
        return d["choices"][0]["message"]["content"], secs, None
    return _anthropic_text(d), secs, None


BACKENDS = {"claude-oauth": call_claude_oauth,
            "minimax-oauth": call_minimax_oauth,
            "api-key": call_api_key}


def ask(p, prompt, max_tokens):
    fn = BACKENDS.get(p["backend"])
    if not fn:
        return {"name": p["name"], "ok": False, "error": f"unknown backend {p['backend']}"}
    text, secs, err = fn(p, prompt, max_tokens)
    return {"name": p["name"], "model": p["model"], "ok": err is None,
            "text": text, "error": err, "secs": secs}


def fusion(providers, prompt, max_tokens=1024):
    active = [p for p in providers if p.get("enabled")]
    if not active:
        return [{"ok": False, "error": "no enabled providers in config"}]
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(active)) as ex:
        futs = [ex.submit(ask, p, prompt, max_tokens) for p in active]
        return [f.result() for f in concurrent.futures.as_completed(futs)]


def load_config(path):
    if not os.path.exists(path):
        sys.exit(f"config not found: {path} (copy providers.example.yaml -> providers.yaml)")
    return yaml.safe_load(open(path))["providers"]


def main():
    args = sys.argv[1:]
    cfg = "providers.yaml"
    if args and args[0] == "--config":
        cfg = args[1]; args = args[2:]
    prompt = " ".join(args).strip() or sys.stdin.read().strip()
    if not prompt:
        sys.exit("usage: fusion.py [--config providers.yaml] 'your prompt'")
    results = fusion(load_config(cfg), prompt)
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
