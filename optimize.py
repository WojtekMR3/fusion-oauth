#!/usr/bin/env python3
"""optimize.py — use ANY model of your choice to rewrite a vague prompt into a
tight, precise, context-grounded one before sending it to your strong model(s).

The optimizer model is whichever provider you pick with --optimizer NAME
(defaults to the first enabled provider in providers.yaml). A cheap/fast model
is a good optimizer, but it's entirely your choice — nothing is hardcoded.

Three wins:
  1. Fewer downstream tokens (strong model answers, doesn't parse mess)
  2. Sharper results (concrete task + constraints + output format)
  3. Fewer FALSE refusals on legitimate work — by supplying YOUR OWN true
     context (supplied via --context), so a model doesn't misread a vague
     request as something it should refuse.

This does NOT fabricate authorization or request harmful output. It only
clarifies legitimate requests with context you provide.

Usage:
  python3 optimize.py "raw prompt"
  python3 optimize.py --optimizer GPT-4o "raw prompt"   # pick which model optimizes
  python3 optimize.py --context "I own this server X; task is admin Y" "raw prompt"
  python3 optimize.py --run  "raw prompt"   # optimize -> send to enabled providers
  echo "raw prompt" | python3 optimize.py
"""
import sys, json
from fusion import ask, fusion, load_config

META = (
    "You are an expert prompt engineer. Rewrite the RAW REQUEST into ONE optimized "
    "prompt for a capable AI assistant.\n\n"
    "Optimize for THREE things:\n"
    "1. CONCISE: cut filler; every token earns its place.\n"
    "2. PRECISE: concrete task, key constraints, exact desired output format/length. "
    "If vague, make reasonable assumptions and note them in one short line.\n"
    "3. GROUNDED: weave in the USER CONTEXT below so the assistant understands the "
    "request is legitimate and does not wrongly refuse it.\n\n"
    "HARD RULES:\n"
    "- Preserve the user's actual intent EXACTLY. Add/drop nothing.\n"
    "- Do not invent authorization beyond the context given; do not request harmful output.\n"
    "- Output ONLY the optimized prompt. No preamble, no quotes.\n\n"
    "USER CONTEXT:\n{context}\n\n"
    "RAW REQUEST:\n{raw}"
)

DEFAULT_CONTEXT = "(none provided — optimize for clarity and precision only)"


def optimize(providers, raw, context, optimizer_name=None):
    # pick the optimizer: named provider, else first enabled
    enabled = [p for p in providers if p.get("enabled")]
    if not enabled:
        sys.exit("no enabled providers in config")
    opt_p = next((p for p in enabled if p["name"] == optimizer_name), enabled[0])
    prompt = META.format(context=context or DEFAULT_CONTEXT, raw=raw)
    r = ask(opt_p, prompt, max_tokens=600)
    return (r["text"].strip() if r["ok"] else None), r


def main():
    args = sys.argv[1:]
    cfg, context, run, optimizer_name = "providers.yaml", "", False, None
    out = []
    while args:
        if args[0] == "--config":
            cfg = args[1]; args = args[2:]
        elif args[0] == "--context":
            context = args[1]; args = args[2:]
        elif args[0] == "--optimizer":
            optimizer_name = args[1]; args = args[2:]
        elif args[0] == "--run":
            run = True; args = args[1:]
        else:
            out.append(args.pop(0))
    raw = " ".join(out).strip() or sys.stdin.read().strip()
    if not raw:
        sys.exit("usage: optimize.py [--optimizer NAME] [--context '...'] [--run] 'raw prompt'")

    providers = load_config(cfg)
    opt, meta = optimize(providers, raw, context, optimizer_name)
    if opt is None:
        sys.exit(json.dumps({"error": "optimizer failed", "detail": meta}, indent=2))

    if not run:
        print(opt)
    else:
        results = fusion(providers, opt, max_tokens=2048)
        print(json.dumps({"optimized_prompt": opt, "optimizer_secs": meta["secs"],
                          "results": results}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
