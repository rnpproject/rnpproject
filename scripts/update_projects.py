#!/usr/bin/env python3
"""Perbarui daftar proyek di README.md dari repositori publik milik akun ini.

Bagian yang diganti berada di antara penanda:
    <!-- PROJECTS:START -->
    <!-- PROJECTS:END -->
"""
import json
import os
import re
import sys
import urllib.request

OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "rnpproject")
SELF_NAME = os.environ.get("GITHUB_REPOSITORY", f"{OWNER}/github-profile").split("/")[-1]
README = os.environ.get("README_PATH", "README.md")
LIMIT = int(os.environ.get("PROJECT_LIMIT", "6"))
EXCLUDE = {SELF_NAME, ".github", OWNER}

START = "<!-- PROJECTS:START -->"
END = "<!-- PROJECTS:END -->"


def fetch_repos():
    url = f"https://api.github.com/users/{OWNER}/repos?per_page=100&type=owner&sort=pushed"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{OWNER}-profile-readme",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def cell(text):
    return (text or "-").replace("|", "\\|").replace("\n", " ").strip() or "-"


def build_table(repos):
    selected = [
        repo
        for repo in repos
        if not repo.get("fork")
        and not repo.get("archived")
        and not repo.get("private")
        and repo["name"] not in EXCLUDE
    ]
    selected.sort(key=lambda repo: repo.get("pushed_at") or "", reverse=True)
    selected = selected[:LIMIT]

    if not selected:
        return "Belum ada proyek publik."

    lines = [
        "| Proyek | Deskripsi | Bahasa | Bintang |",
        "| --- | --- | --- | ---: |",
    ]
    for repo in selected:
        lines.append(
            "| [{name}]({url}) | {desc} | {lang} | {stars} |".format(
                name=repo["name"],
                url=repo["html_url"],
                desc=cell(repo.get("description")),
                lang=cell(repo.get("language")),
                stars=repo.get("stargazers_count", 0),
            )
        )
    return "\n".join(lines)


def update_readme(table):
    with open(README, encoding="utf-8") as handle:
        content = handle.read()

    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(content):
        sys.exit(f"Penanda {START} ... {END} tidak ditemukan di {README}")

    replacement = f"{START}\n{table}\n{END}"
    updated = pattern.sub(lambda _: replacement, content)

    if updated == content:
        print("Tidak ada perubahan.")
        return
    with open(README, "w", encoding="utf-8") as handle:
        handle.write(updated)
    print("README diperbarui.")


def main(fetch=fetch_repos):
    update_readme(build_table(fetch()))


if __name__ == "__main__":
    main()
