"""
TryIT Question Engine — Providers
====================================
Thin wrapper around several free-tier LLM providers, with automatic
failover (try the next provider if one is rate-limited) and exponential
backoff. All keys come from environment variables / GitHub Secrets —
NEVER hardcode a key in this file, this repo is public.

Required environment variables (set these as GitHub Secrets):
  CEREBRAS_API_KEY
  GROQ_API_KEY
  GEMINI_API_KEY
  OPENROUTER_API_KEY
  MISTRAL_API_KEY

Any of these can be left unset — the failover chain just skips providers
with no key configured. At least ONE must be set for anything to work.
"""

import os
import time
import json
import random
import threading
import requests

from config import PROVIDER_MODELS

REQUEST_TIMEOUT = 60
MAX_RETRIES_PER_PROVIDER = 2


def _env(name):
    return os.environ.get(name, "").strip()


# ──────────────────────────────────────────────────────────
# Individual provider callers. Each returns (text_or_None, status_string).
# status_string is one of: "ok", "rate_limit", "auth_error", "error"
# ──────────────────────────────────────────────────────────

def call_cerebras(prompt, model=None):
    key = _env("CEREBRAS_API_KEY")
    if not key:
        return None, "no_key"
    model = model or PROVIDER_MODELS["cerebras"]
    try:
        r = requests.post(
            "https://api.cerebras.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.7, "max_tokens": 12000},
            timeout=REQUEST_TIMEOUT,
        )
        return _handle_openai_style_response(r)
    except requests.RequestException as e:
        return None, f"error:{e}"


def call_groq(prompt, model=None):
    key = _env("GROQ_API_KEY")
    if not key:
        return None, "no_key"
    model = model or PROVIDER_MODELS["groq_fast"]
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.7, "max_tokens": 12000},
            timeout=REQUEST_TIMEOUT,
        )
        return _handle_openai_style_response(r)
    except requests.RequestException as e:
        return None, f"error:{e}"


def call_gemini(prompt, model=None):
    key = _env("GEMINI_API_KEY")
    if not key:
        return None, "no_key"
    model = model or PROVIDER_MODELS["gemini"]
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code == 429:
            return None, "rate_limit"
        if r.status_code in (401, 403):
            return None, "auth_error"
        if r.status_code != 200:
            return None, f"error:{r.status_code}"
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text, "ok"
    except (requests.RequestException, KeyError, IndexError) as e:
        return None, f"error:{e}"


def call_openrouter(prompt, model=None):
    key = _env("OPENROUTER_API_KEY")
    if not key:
        return None, "no_key"
    model = model or PROVIDER_MODELS["openrouter"]
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.7, "max_tokens": 12000},
            timeout=REQUEST_TIMEOUT,
        )
        return _handle_openai_style_response(r)
    except requests.RequestException as e:
        return None, f"error:{e}"


def call_mistral(prompt, model=None):
    key = _env("MISTRAL_API_KEY")
    if not key:
        return None, "no_key"
    model = model or PROVIDER_MODELS["mistral"]
    try:
        r = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.7, "max_tokens": 12000},
            timeout=REQUEST_TIMEOUT,
        )
        return _handle_openai_style_response(r)
    except requests.RequestException as e:
        return None, f"error:{e}"


def call_cohere(prompt, model=None):
    """Cohere's free trial API key tier — verify current rate limits
    against Cohere's docs before relying on this at volume, terms shift
    over time. Uses the v2 chat endpoint."""
    key = _env("COHERE_API_KEY")
    if not key:
        return None, "no_key"
    model = model or PROVIDER_MODELS.get("cohere", "command-r-plus")
    try:
        r = requests.post(
            "https://api.cohere.com/v2/chat",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.7, "max_tokens": 12000},
            timeout=REQUEST_TIMEOUT,
        )
        if r.status_code == 429:
            return None, "rate_limit"
        if r.status_code in (401, 403):
            return None, "auth_error"
        if r.status_code != 200:
            return None, f"error:{r.status_code}:{r.text[:150]}"
        data = r.json()
        text = data["message"]["content"][0]["text"]
        return text, "ok"
    except (requests.RequestException, KeyError, IndexError, json.JSONDecodeError) as e:
        return None, f"error:{e}"


def call_huggingface(prompt, model=None):
    """HuggingFace's free-tier router endpoint (OpenAI-compatible shape)
    — verify current free-tier model availability/limits against HF's
    docs, this also shifts over time."""
    key = _env("HUGGINGFACE_API_KEY")
    if not key:
        return None, "no_key"
    model = model or PROVIDER_MODELS.get("huggingface", "meta-llama/Llama-3.3-70B-Instruct")
    try:
        r = requests.post(
            "https://router.huggingface.co/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.7, "max_tokens": 12000},
            timeout=REQUEST_TIMEOUT,
        )
        return _handle_openai_style_response(r)
    except requests.RequestException as e:
        return None, f"error:{e}"


def call_azure_openai(prompt, model=None):
    """Azure OpenAI — deliberately placed LAST in CONCEPT_CHAIN, meant
    to be used only when every free provider fails, to keep Azure
    credit usage minimal rather than routine. Requires all three of
    AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT to
    be set — verify the exact api-version against your resource's
    current supported versions if this errors."""
    key = _env("AZURE_OPENAI_KEY")
    endpoint = _env("AZURE_OPENAI_ENDPOINT").rstrip("/")
    deployment = _env("AZURE_OPENAI_DEPLOYMENT")
    if not key or not endpoint or not deployment:
        return None, "no_key"
    try:
        r = requests.post(
            f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version=2024-08-01-preview",
            headers={"api-key": key, "Content-Type": "application/json"},
            json={"messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.7, "max_tokens": 12000},
            timeout=REQUEST_TIMEOUT,
        )
        return _handle_openai_style_response(r)
    except requests.RequestException as e:
        return None, f"error:{e}"


def _handle_openai_style_response(r):
    if r.status_code == 429:
        return None, "rate_limit"
    if r.status_code in (401, 403):
        return None, "auth_error"
    if r.status_code != 200:
        return None, f"error:{r.status_code}:{r.text[:150]}"
    try:
        data = r.json()
        return data["choices"][0]["message"]["content"], "ok"
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        return None, f"error:parse:{e}"


# ──────────────────────────────────────────────────────────
# FAILOVER CHAINS — order matters. Generation favors high-volume free
# providers; verification favors stronger-reasoning models.
# ──────────────────────────────────────────────────────────
GENERATION_CHAIN = [call_cerebras, call_groq, call_openrouter, call_mistral]
VERIFICATION_CHAIN_1 = [call_groq, call_cerebras]          # uses groq_strong model, see call_with_failover
VERIFICATION_CHAIN_2 = [call_gemini, call_mistral, call_openrouter]
TRANSLATION_CHAIN = [call_mistral, call_cerebras, call_groq, call_openrouter]

# Concept-teaching content chain — 6 free providers rotate as the main
# workhorse (same rotated_chain() spread-load pattern as GENERATION_CHAIN),
# with Azure deliberately LAST: only invoked if every free provider in
# the chain fails, keeping Azure credit usage close to zero in normal
# operation rather than routine per-call usage.
CONCEPT_CHAIN = [call_cerebras, call_groq, call_gemini, call_mistral,
                  call_openrouter, call_cohere, call_huggingface, call_azure_openai]

# ──────────────────────────────────────────────────────────
# CONCURRENT-JOB PROVIDER ROTATION
# When jobs run in parallel (see pipeline.py's ThreadPoolExecutor), every
# thread calling call_with_failover(prompt, GENERATION_CHAIN) would
# otherwise all hit Cerebras first at the same moment, immediately
# contending for Cerebras's own rate limit before any of them fall
# through to the other three providers — wasting the fact that Groq,
# OpenRouter, and Mistral have entirely separate quotas that could be
# used AT THE SAME TIME instead of sitting idle.
#
# _next_chain_offset() hands out a rotating starting index (thread-safe
# via the lock) so concurrent jobs actually start on DIFFERENT
# providers. Each job's chain still wraps around to try all providers
# if its first choice fails — this only changes which one goes first.
# ──────────────────────────────────────────────────────────
_chain_offset_lock = threading.Lock()
_chain_offset_counter = 0


def _next_chain_offset(chain_length: int) -> int:
    global _chain_offset_counter
    with _chain_offset_lock:
        offset = _chain_offset_counter % chain_length
        _chain_offset_counter += 1
    return offset


def rotated_chain(chain: list) -> list:
    """Returns the chain reordered to start at a rotating offset, wrapping
    around, so concurrent callers spread across providers instead of all
    starting at index 0 simultaneously."""
    offset = _next_chain_offset(len(chain))
    return chain[offset:] + chain[:offset]


def call_with_failover(prompt, chain, model_override=None, label="call"):
    """Try each provider in order. On rate_limit/auth_error/error, back off
    briefly and move to the next provider. Returns (text, provider_name) or
    (None, None) if every provider in the chain failed.

    NOTE: model_override is provider-specific (e.g. a Groq model id isn't a
    valid Cerebras model id), so it must ONLY be applied to the first
    provider in the chain — never carried over to the fallback providers
    that follow it, or they'll get called with a model name that doesn't
    exist on their platform."""
    for attempt, fn in enumerate(chain):
        use_override = model_override if attempt == 0 else None
        for retry in range(MAX_RETRIES_PER_PROVIDER):
            text, status = fn(prompt, use_override) if use_override else fn(prompt)
            if status == "ok" and text:
                return text, fn.__name__
            if status == "no_key":
                break  # don't retry a provider with no key configured, just skip it
            if status == "rate_limit":
                backoff = (2 ** retry) + random.uniform(0, 1)
                time.sleep(backoff)
                continue
            if status == "auth_error":
                print(f"  [{label}] {fn.__name__} auth error — check the API key secret")
                break
            # generic error — one quick retry then move on
            time.sleep(1)
    return None, None
