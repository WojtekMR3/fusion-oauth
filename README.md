# fusion-oauth

**Prompt several AI models at once, compare their answers — using your existing subscriptions, not just API keys.**

Inspired by [OpenRouter's Fusion](https://openrouter.ai/) (one prompt → a panel of models → judge & synthesize). The twist: **fusion-oauth works with your OAuth subscriptions** — your Claude Code (Max/Pro) and MiniMax logins — so you can fan a prompt across models you *already pay a flat fee for*, with **no per-token API billing**. And if you do want API-key models too (GPT, DeepSeek, anything OpenAI/Anthropic-compatible), those drop in side by side.

> **No keys or tokens are ever stored or committed.** Credentials are read at runtime from your local login files or from environment variables you control. `providers.yaml` is gitignored.

## Why it's different

- **OAuth subscriptions, not just API keys** — most multi-model tools assume you have (and pay for) API keys for everything. fusion-oauth uses the OAuth sessions from tools you already run (Claude Code, MiniMax), so your flat-rate subscription becomes a programmable model.
- **Mix subscriptions *and* API keys** — run Claude (OAuth) + MiniMax (OAuth) + GPT-4o + DeepSeek (API keys) in the **same panel**, all in parallel.
- **Bring any compatible model** — DeepSeek, OpenAI, OpenRouter, local servers… anything speaking the OpenAI- or Anthropic-style `/v1/messages` / `/chat/completions` shape.
- **Prompt optimizer included** — an optional pre-pass where **a model of your choice** rewrites a vague prompt into a tight, precise one: fewer downstream tokens, sharper answers, and fewer *false refusals* on legitimate work (by adding context **you** supply).

## How it works

Each provider declares a `backend`:

| backend | reads credentials from | use for |
|---|---|---|
| `claude-oauth` | `~/.claude/.credentials.json` | your Claude Code (Max/Pro) login |
| `minimax-oauth` | `~/.hermes/auth.json` | your MiniMax OAuth login |
| `api-key` | an env var you name | GPT, DeepSeek, OpenRouter, local — any compatible endpoint |

All enabled providers are queried **concurrently**; answers come back together so you can compare side by side (or pipe them into your own judge/synthesis step).

## Install

```bash
git clone https://github.com/<you>/fusion-oauth.git
cd fusion-oauth
pip install pyyaml
cp providers.example.yaml providers.yaml   # then edit; providers.yaml is gitignored
```

## Configure

`providers.yaml` — enable what you have. Example mixing OAuth subs and API keys:

```yaml
providers:
  - name: Claude-Opus       # OAuth subscription
    backend: claude-oauth
    model: claude-opus-4-20250514
    enabled: true

  - name: MiniMax-M3        # OAuth subscription
    backend: minimax-oauth
    model: MiniMax-M3
    enabled: true

  - name: GPT-4o            # API key
    backend: api-key
    model: gpt-4o
    endpoint: https://api.openai.com/v1/chat/completions
    api_key_env: OPENAI_API_KEY
    enabled: true

  - name: DeepSeek          # API key
    backend: api-key
    model: deepseek-chat
    endpoint: https://api.deepseek.com/v1/chat/completions
    api_key_env: DEEPSEEK_API_KEY
    enabled: true
```

API keys come from environment variables you set (`export OPENAI_API_KEY=...`) — never from the config file.

## Usage

```bash
# fuse: ask all enabled providers in parallel
python3 fusion.py "Explain the trade-offs of event-driven vs polling architectures."

# optimize a vague prompt (prints the improved prompt)
python3 optimize.py "make my service use less memory"

# pick which model does the optimizing (any enabled provider, by name)
python3 optimize.py --optimizer MiniMax-M3 "make my service use less memory"

# optimize WITH your own legitimate context, then run against all models
python3 optimize.py --context "I own and admin this Linux server; reduce RSS of my own app" --run "make my service use less ram"
```

Output is JSON: each provider's answer, latency, and any error.

## The prompt optimizer & "false refusals"

Models sometimes refuse a *legitimate* request because it's vague and pattern-matches to something risky. The optimizer fixes this the honest way: it adds the **true context you supply via `--context`** (e.g. "this is my own server / my own account") so the model understands the request is legitimate self-administration.

It will **not** fabricate authorization or coax a model into producing genuinely harmful content — it only clarifies legitimate requests with context that you, the owner, provide.

## Notes

- OAuth access tokens expire periodically; if you get a 401, re-login with the respective tool and retry.
- `providers.yaml`, `*.credentials.json`, `auth.json`, `.env`, and `*token*`/`*secret*` files are gitignored by default.
- Credits: the panel/judge concept is OpenRouter's Fusion; this project adapts it to OAuth subscriptions + arbitrary API-key backends.

## License

MIT
