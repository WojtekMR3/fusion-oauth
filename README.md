<div align="center">

# 🔮 fusion-oauth

### Prompt many AI models at once — with the subscriptions you already pay for.

**One prompt → a panel of models → answers side by side.**
[OpenRouter Fusion](https://openrouter.ai/)'s idea, reimagined for **OAuth subscriptions** (Claude Code, MiniMax) **and** API keys (GPT, DeepSeek, OpenRouter, local).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/WojtekMR3/fusion-oauth/pulls)
![No keys committed](https://img.shields.io/badge/secrets-never%20committed-success)
![Multi-Model](https://img.shields.io/badge/models-Claude%20%7C%20GPT%20%7C%20DeepSeek%20%7C%20MiniMax-8A2BE2)

</div>

---

## ✨ Why fusion-oauth?

Most multi-model tools assume you hold (and pay per-token for) an API key for *every* model. **fusion-oauth is different:** it taps the **OAuth sessions you already have** from tools like Claude Code and MiniMax — so your flat-rate subscription becomes a programmable model you can fan prompts across. Want API-key models too? Drop them into the same panel.

| | Typical multi-model tool | 🔮 **fusion-oauth** |
|---|:---:|:---:|
| Use OAuth subscriptions (Claude Code, MiniMax) | ❌ | ✅ |
| Use API keys (GPT, DeepSeek, OpenRouter, local) | ✅ | ✅ |
| Mix subscriptions **and** keys in one panel | ❌ | ✅ |
| Parallel queries, side-by-side answers | sometimes | ✅ |
| Built-in prompt optimizer (any model) | ❌ | ✅ |
| Secrets never stored or committed | varies | ✅ |

---

## 🚀 Features

- **🔑 OAuth-native** — use your Claude Code (Max/Pro) and MiniMax logins directly; **no per-token API billing** for those.
- **🧩 Mix-and-match backends** — OAuth subs **+** API keys (OpenAI, DeepSeek, OpenRouter, local servers) in the **same parallel panel**.
- **⚡ Parallel by default** — every enabled model is queried concurrently; compare answers instantly.
- **🪄 Prompt optimizer** — an optional pre-pass where **a model of your choice** rewrites a vague prompt into a tight, precise one: fewer tokens, sharper answers, fewer *false refusals* on legitimate work (using context **you** supply).
- **🔒 Secrets-safe** — credentials are read at runtime from your local login files or env vars; `providers.yaml` and all token/key files are gitignored.

---

## 📦 Install

```bash
git clone https://github.com/WojtekMR3/fusion-oauth.git
cd fusion-oauth
pip install pyyaml
cp providers.example.yaml providers.yaml   # edit it — providers.yaml is gitignored
```

---

## ⚙️ How it works

Each provider declares a `backend`:

| backend | reads credentials from | use for |
|---|---|---|
| `claude-oauth` | `~/.claude/.credentials.json` | your Claude Code (Max/Pro) login |
| `minimax-oauth` | `~/.hermes/auth.json` | your MiniMax OAuth login |
| `api-key` | an env var you name | GPT, DeepSeek, OpenRouter, local — any compatible endpoint |

All enabled providers are queried **concurrently**; answers come back together for easy comparison — or pipe the JSON into your own judge/synthesis step.

### Example `providers.yaml` — mixing subs and keys

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

> API keys come from environment variables you set (`export OPENAI_API_KEY=...`) — never from the config file.

---

## 💻 Usage

```bash
# Fuse: ask every enabled model in parallel
python3 fusion.py "Explain the trade-offs of event-driven vs polling architectures."

# Optimize a vague prompt (prints the improved prompt)
python3 optimize.py "make my service use less memory"

# Pick which model does the optimizing — any enabled provider, by name
python3 optimize.py --optimizer MiniMax-M3 "make my service use less memory"

# Optimize with your own legitimate context, then run against all models
python3 optimize.py --context "I own and admin this Linux server; reduce RSS of my own app" --run "make my service use less ram"
```

Output is JSON: each provider's answer, latency, and any error.

---

## 🪄 The prompt optimizer & "false refusals"

Models sometimes refuse a **legitimate** request because it's vague and pattern-matches to something risky. The optimizer fixes this honestly: it folds in the **true context you supply via `--context`** (e.g. *"this is my own server / my own account"*) so the model understands the request is legitimate self-administration.

It will **not** fabricate authorization or coax a model into producing genuinely harmful content — it only clarifies *legitimate* requests with context **you, the owner, provide.**

---

## ❓ FAQ

**Do I need API keys?** No — OAuth subscriptions (Claude Code, MiniMax) work on their own. API keys are optional extras.

**Are my tokens uploaded anywhere?** Never. They're read at runtime from your local login files or env vars. `providers.yaml`, `*.credentials.json`, `auth.json`, `.env`, and `*token*`/`*secret*` files are gitignored.

**My request returned 401.** OAuth tokens expire periodically — re-login with the relevant tool and retry.

**Which models are supported?** Anything speaking the OpenAI- or Anthropic-style `/chat/completions` or `/v1/messages` shape: Claude, GPT, DeepSeek, MiniMax, OpenRouter, local servers, and more.

---

## 🙏 Credits

The panel/judge concept is [OpenRouter's Fusion](https://openrouter.ai/). **fusion-oauth** adapts it to OAuth subscriptions plus arbitrary API-key backends.

## 📄 License

[MIT](LICENSE) © 2026 WojtekMR3

---

<div align="center">

**Keywords:** multi-model LLM · AI model fusion · OAuth · Claude Code · GPT · DeepSeek · MiniMax · OpenRouter alternative · parallel LLM prompting · prompt optimizer

⭐ **Star this repo if it's useful!**

</div>
