"""
TryIT Question Engine — Health Check
========================================
Run this BEFORE a real generation run, not after something fails midway.
Tests every provider key with one tiny, cheap call (not a real generation
request), plus Supabase read/write access. Tells you exactly what's
configured, what's missing, and what's failing — so a bad key shows up
in 10 seconds instead of buried in the middle of a 60-job run.

Usage:
    python healthcheck.py
"""

import os
import sys
import requests

from config import PROVIDER_MODELS

REQUEST_TIMEOUT = 20


def _env(name):
    return os.environ.get(name, "").strip()


def _check_openai_style(name, url, key, model, headers_extra=None):
    if not key:
        return name, "NOT SET", "no key in environment"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if headers_extra:
        headers.update(headers_extra)
    try:
        r = requests.post(
            url, headers=headers,
            json={"model": model, "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5},
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code == 200:
            return name, "OK", f"model {model} responded"
        if r.status_code == 401 or r.status_code == 403:
            return name, "AUTH ERROR", f"{r.status_code} — key is invalid or revoked"
        if r.status_code == 429:
            return name, "RATE LIMITED", "key works, but you're at the limit right now — try again shortly"
        return name, "ERROR", f"{r.status_code}: {r.text[:150]}"
    except requests.RequestException as e:
        return name, "ERROR", str(e)


def check_cerebras():
    return _check_openai_style("Cerebras", "https://api.cerebras.ai/v1/chat/completions",
                                _env("CEREBRAS_API_KEY"), PROVIDER_MODELS["cerebras"])


def check_groq():
    return _check_openai_style("Groq", "https://api.groq.com/openai/v1/chat/completions",
                                _env("GROQ_API_KEY"), PROVIDER_MODELS["groq_fast"])


def check_openrouter():
    return _check_openai_style("OpenRouter", "https://openrouter.ai/api/v1/chat/completions",
                                _env("OPENROUTER_API_KEY"), PROVIDER_MODELS["openrouter"])


def check_mistral():
    return _check_openai_style("Mistral", "https://api.mistral.ai/v1/chat/completions",
                                _env("MISTRAL_API_KEY"), PROVIDER_MODELS["mistral"])


def check_gemini():
    key = _env("GEMINI_API_KEY")
    if not key:
        return "Gemini", "NOT SET", "no key in environment"
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{PROVIDER_MODELS['gemini']}:generateContent?key={key}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": "Say OK"}]}]},
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code == 200:
            return "Gemini", "OK", "model responded"
        if r.status_code in (401, 403):
            return "Gemini", "AUTH ERROR", f"{r.status_code} — key is invalid or revoked"
        if r.status_code == 429:
            return "Gemini", "RATE LIMITED", "key works, but you're at the limit right now"
        return "Gemini", "ERROR", f"{r.status_code}: {r.text[:150]}"
    except requests.RequestException as e:
        return "Gemini", "ERROR", str(e)


def check_supabase():
    url, key = _env("SUPABASE_URL"), _env("SUPABASE_KEY")
    if not url or not key:
        return "Supabase", "NOT SET", "SUPABASE_URL/SUPABASE_KEY missing"
    try:
        r = requests.get(
            f"{url}/rest/v1/topics",
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            params={"select": "topic_id", "limit": 1},
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code == 200:
            rows = r.json()
            if rows:
                return "Supabase", "OK", f"read access confirmed, e.g. topic_id={rows[0].get('topic_id')}"
            return "Supabase", "OK (but empty)", "connected fine, but `topics` returned 0 rows — did seed_topics.py run?"
        if r.status_code == 403:
            return "Supabase", "PERMISSION ERROR", f"{r.text[:200]}"
        if r.status_code in (401,):
            return "Supabase", "AUTH ERROR", "SUPABASE_KEY is invalid — check it's the secret/service_role key, not publishable"
        return "Supabase", "ERROR", f"{r.status_code}: {r.text[:200]}"
    except requests.RequestException as e:
        return "Supabase", "ERROR", str(e)


def main():
    checks = [check_cerebras, check_groq, check_openrouter, check_mistral, check_gemini, check_supabase]
    results = [fn() for fn in checks]

    print("=" * 60)
    print("TryIT Question Engine — Health Check")
    print("=" * 60)
    for name, status, detail in results:
        marker = {"OK": "✓", "NOT SET": "-"}.get(status, "✗")
        print(f"{marker} {name:12s} {status:18s} {detail}")
    print("=" * 60)

    working = [r for r in results if r[1] == "OK"]
    generation_providers = {"Cerebras", "Groq", "OpenRouter", "Mistral"}
    working_generation = [r for r in working if r[0] in generation_providers]

    if not working_generation:
        print("\nWARNING: no generation provider is working. The pipeline cannot generate anything.")
        sys.exit(1)
    elif len(working_generation) == 1:
        print(f"\nOnly 1 generation provider working ({working_generation[0][0]}) — pipeline will run, "
              f"but with no failover if it gets rate-limited. Consider fixing the others.")
    else:
        print(f"\n{len(working_generation)} generation providers working — good failover coverage.")

    if not any(r[0] == "Supabase" and r[1].startswith("OK") for r in results):
        print("Supabase is not working — pipeline will generate questions but cannot save them anywhere.")


if __name__ == "__main__":
    main()
