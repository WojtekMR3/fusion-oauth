#!/usr/bin/env python3
"""fuse.py — OAuth-native clone of OpenRouter Fusion's deliberation pipeline.

Fusion turns your prompt into a small multi-model deliberation:
  1. PANEL  — a panel of models analyzes your prompt IN PARALLEL.
  2. JUDGE  — a judge model synthesizes their responses into a structured
              analysis (consensus, contradictions, partial coverage, unique
              insights, blind spots) and writes the final answer from it.

This mirrors openrouter/fusion's mechanism, but every model runs on YOUR
credentials — OAuth subscriptions (Claude Code, MiniMax) and/or API keys
(GPT, DeepSeek, OpenRouter, local) — defined in providers.yaml.

Panel = every provider with `panel: true` (falls back to all enabled).
Judge = the provider named `judge: true` (falls back to the first panel member).

Usage:
  python3 fuse.py "your question"
  python3 fuse.py --json "your question"          # full structured output as JSON
  python3 fuse.py --judge Claude-Opus "your q"    # override the judge model
  echo "your question" | python3 fuse.py
"""
import sys, json
from fusion import ask, load_config

PANEL_PROMPT = (
    "You are an expert analyst on a deliberation panel. Analyze the user's QUESTION "
    "rigorously and independently. Give your best reasoning, key evidence, explicit "
    "assumptions, and where you might be wrong. Be concrete.\n\nQUESTION:\n{q}"
)

JUDGE_PROMPT = (
    "You are the JUDGE in a multi-model deliberation. Several expert models each "
    "answered the same QUESTION independently. Synthesize their PANEL RESPONSES into "
    "a final answer. Do NOT just average them — reason about them.\n\n"
    "Produce, in this order:\n"
    "## Consensus\nPoints where the panel agrees (higher confidence).\n"
    "## Contradictions\nWhere they conflict — name the crux and say which side is better supported.\n"
    "## Partial coverage\nImportant angles only some models addressed.\n"
    "## Unique insights\nValuable points raised by a single model.\n"
    "## Blind spots\nWhat NONE of them addressed but should have.\n"
    "## Final answer\nThe definitive, actionable answer, written FROM the analysis above.\n\n"
    "QUESTION:\n{q}\n\nPANEL RESPONSES:\n{panel}"
)


def run_fusion(providers, question, judge_override=None, max_tokens=2048):
    enabled = [p for p in providers if p.get("enabled")]
    panel = [p for p in enabled if p.get("panel")] or enabled
    if not panel:
        sys.exit("no enabled providers in config")

    # 1. PANEL — parallel
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(panel)) as ex:
        futs = {ex.submit(ask, p, PANEL_PROMPT.format(q=question), max_tokens): p
                for p in panel}
        panel_results = [f.result() for f in concurrent.futures.as_completed(futs)]

    ok = [r for r in panel_results if r["ok"]]
    if not ok:
        return {"panel": panel_results, "judge": None,
                "error": "all panel members failed"}

    # 2. JUDGE — synthesize
    judge = None
    if judge_override:
        judge = next((p for p in enabled if p["name"] == judge_override), None)
    if judge is None:
        judge = next((p for p in enabled if p.get("judge")), None)
    if judge is None:
        judge = next((p for p in panel if p["name"] == ok[0]["name"]), panel[0])

    panel_text = "\n\n".join(f"### {r['name']} ({r.get('model')})\n{r['text']}" for r in ok)
    jres = ask(judge, JUDGE_PROMPT.format(q=question, panel=panel_text), max_tokens=max_tokens)

    return {"question": question,
            "panel": [{"name": r["name"], "model": r.get("model"), "ok": r["ok"],
                       "secs": r.get("secs"), "text": r.get("text"), "error": r.get("error")}
                      for r in panel_results],
            "judge_model": judge["name"],
            "judge": jres}


def main():
    args = sys.argv[1:]
    cfg, as_json, judge_override = "providers.yaml", False, None
    out = []
    while args:
        if args[0] == "--config":
            cfg = args[1]; args = args[2:]
        elif args[0] == "--judge":
            judge_override = args[1]; args = args[2:]
        elif args[0] == "--json":
            as_json = True; args = args[1:]
        else:
            out.append(args.pop(0))
    question = " ".join(out).strip() or sys.stdin.read().strip()
    if not question:
        sys.exit("usage: fuse.py [--judge NAME] [--json] 'your question'")

    result = run_fusion(load_config(cfg), question, judge_override)

    if as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False)); return

    # human-readable
    print(f"\n{'='*60}\n🔮 FUSION — {len(result['panel'])} panelists → judge: {result.get('judge_model')}\n{'='*60}")
    for r in result["panel"]:
        status = f"✓ {r['secs']}s" if r["ok"] else f"✗ {r['error']}"
        print(f"  • {r['name']} ({r['model']}): {status}")
    j = result.get("judge")
    if j and j.get("ok"):
        print(f"\n{'-'*60}\n{j['text']}\n")
    else:
        print(f"\n[judge failed: {j.get('error') if j else result.get('error')}]")


if __name__ == "__main__":
    main()
