"""Shared GitHub API helpers for the profile-README generator scripts."""

import json
import os
import urllib.request

GITHUB_USERNAME = "shre2201"
_BASE_HEADERS = {"User-Agent": "profile-readme-generator", "Accept": "application/vnd.github+json"}


def _token_headers():
    headers = dict(_BASE_HEADERS)
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def get_json(url):
    request = urllib.request.Request(url, headers=_token_headers())
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read())


def graphql(query, variables=None):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required for GraphQL requests")
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={**_token_headers(), "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.loads(response.read())
    if "errors" in payload:
        raise RuntimeError(str(payload["errors"]))
    return payload
