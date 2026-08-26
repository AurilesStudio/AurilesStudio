#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genere dark_mode.svg et light_mode.svg pour le README de profil GitHub.

Usage :
    python3 today.py            # interroge l'API GitHub (necessite ACCESS_TOKEN)
    python3 today.py --demo     # chiffres factices, aucun reseau (pour tester le rendu)

Variables d'environnement attendues en mode reel :
    ACCESS_TOKEN  : personal access token GitHub (scopes repo + read:user)
    USER_NAME     : pseudo GitHub (sinon config.USERNAME)
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

import config
import svg_builder

API = "https://api.github.com/graphql"
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
DEMO = "--demo" in sys.argv

TOKEN = os.environ.get("ACCESS_TOKEN", "")
USER = os.environ.get("USER_NAME") or config.USERNAME


# --------------------------------------------------------------------------- utils
def fr(n):
    """1234567 -> '1 234 567' (espace fine insecable)."""
    return "{:,}".format(int(n)).replace(",", " ")


def query(q, variables=None, retries=4):
    payload = json.dumps({"query": q, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        API, data=payload,
        headers={"Authorization": "bearer " + TOKEN,
                 "Content-Type": "application/json",
                 "User-Agent": "profile-readme-generator"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                data = json.loads(r.read().decode())
            if "errors" in data:
                raise RuntimeError(data["errors"])
            return data["data"]
        except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError) as exc:
            if attempt == retries - 1:
                raise
            wait = 2 ** attempt
            print("  ! %s -> nouvelle tentative dans %ss" % (exc, wait))
            time.sleep(wait)


# --------------------------------------------------------------------------- API
Q_USER = """
query($login:String!){
  user(login:$login){
    id name createdAt
    followers{totalCount}
    starredRepositories{totalCount}
    contributionsCollection{ totalCommitContributions restrictedContributionsCount }
    pub:repositories(privacy:PUBLIC ownerAffiliations:OWNER){totalCount}
    priv:repositories(privacy:PRIVATE ownerAffiliations:OWNER){totalCount}
  }
}"""

Q_REPOS = """
query($login:String!,$cursor:String){
  user(login:$login){
    repositories(first:100 after:$cursor ownerAffiliations:OWNER isFork:false
                 orderBy:{field:PUSHED_AT direction:DESC}){
      pageInfo{hasNextPage endCursor}
      nodes{
        nameWithOwner stargazerCount isPrivate
        languages(first:8 orderBy:{field:SIZE direction:DESC}){
          edges{size node{name color}}
        }
        defaultBranchRef{ target{ ... on Commit { history(author:{id:$__ID__}){totalCount} } } }
      }
    }
  }
}"""

Q_HISTORY = """
query($owner:String!,$name:String!,$id:ID!,$cursor:String){
  repository(owner:$owner name:$name){
    defaultBranchRef{ target{ ... on Commit {
      history(first:100 after:$cursor author:{id:$id}){
        pageInfo{hasNextPage endCursor}
        nodes{ additions deletions }
      }}}}
  }
}"""

Q_YEAR = """
query($login:String!,$from:DateTime!,$to:DateTime!){
  user(login:$login){
    contributionsCollection(from:$from to:$to){
      totalCommitContributions restrictedContributionsCount
    }
  }
}"""


def fetch_repos(login, user_id):
    q = Q_REPOS.replace("$__ID__", '"%s"' % user_id)
    cursor, out = None, []
    while True:
        d = query(q, {"login": login, "cursor": cursor})["user"]["repositories"]
        out += d["nodes"]
        if not d["pageInfo"]["hasNextPage"]:
            return out
        cursor = d["pageInfo"]["endCursor"]


def commits_all_time(login, created_at):
    start = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    total = 0
    for year in range(start.year, now.year + 1):
        a = max(start, datetime(year, 1, 1, tzinfo=timezone.utc))
        b = min(now, datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc))
        if a >= b:
            continue
        c = query(Q_YEAR, {"login": login,
                           "from": a.strftime("%Y-%m-%dT%H:%M:%SZ"),
                           "to": b.strftime("%Y-%m-%dT%H:%M:%SZ")})
        cc = c["user"]["contributionsCollection"]
        total += cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
    return total


def lines_of_code(repos, user_id):
    """Additions/suppressions signees par toi, avec cache par depot."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, "loc.json")
    cache = {}
    if os.path.exists(path):
        try:
            cache = json.load(open(path))
        except Exception:
            cache = {}

    add = dele = 0
    for repo in repos:
        ref = repo.get("defaultBranchRef")
        n = 0
        if ref and ref.get("target"):
            n = ref["target"]["history"]["totalCount"]
        key = repo["nameWithOwner"]
        if n == 0:
            continue
        hit = cache.get(key)
        if hit and hit.get("commits") == n:
            add += hit["add"]
            dele += hit["del"]
            continue
        owner, name = key.split("/", 1)
        a = d = 0
        cursor = None
        while True:
            res = query(Q_HISTORY, {"owner": owner, "name": name,
                                    "id": user_id, "cursor": cursor})
            h = res["repository"]["defaultBranchRef"]["target"]["history"]
            for c in h["nodes"]:
                a += c["additions"]
                d += c["deletions"]
            if not h["pageInfo"]["hasNextPage"]:
                break
            cursor = h["pageInfo"]["endCursor"]
        cache[key] = {"commits": n, "add": a, "del": d}
        add += a
        dele += d
        print("  · %s : +%d / -%d" % (key, a, d))

    json.dump(cache, open(path, "w"), indent=1)
    return add, dele


def language_mix(repos, top=6):
    sizes = {}
    colors = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            nm = e["node"]["name"]
            sizes[nm] = sizes.get(nm, 0) + e["size"]
            if e["node"]["color"]:
                colors[nm] = e["node"]["color"]
    if not sizes:
        return None
    total = sum(sizes.values())
    ranked = sorted(sizes.items(), key=lambda kv: -kv[1])
    brand = getattr(config, "BRAND_LANGUAGE_COLORS", False)
    ramp = getattr(config, "BRAND_RAMP", config.PALETTE_FALLBACK)
    out = []
    for i, (nm, sz) in enumerate(ranked[:top - 1]):
        if brand:
            col = ramp[i % len(ramp)]
        else:
            col = config.LANGUAGE_COLORS.get(nm) or colors.get(nm) \
                or config.PALETTE_FALLBACK[i % len(config.PALETTE_FALLBACK)]
        out.append((nm, round(sz * 100.0 / total, 1), col))
    rest = sum(sz for _, sz in ranked[top - 1:])
    if rest:
        out.append(("Autres", round(rest * 100.0 / total, 1),
                    ramp[-1] if brand else "#6e7681"))
    return out


# --------------------------------------------------------------------------- data
def uptime_label(created_at):
    start = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
    now = datetime.utcnow()
    months = (now.year - start.year) * 12 + (now.month - start.month)
    if now.day < start.day:
        months -= 1
    y, m = divmod(max(months, 0), 12)
    days = (now - start).days
    bits = []
    if y:
        bits.append("%d an%s" % (y, "s" if y > 1 else ""))
    bits.append("%d mois" % m)
    return "%s  (%s jours)" % (", ".join(bits), fr(days))


def font_face():
    """Embarque JetBrains Mono dans le SVG si le fichier est present."""
    rel = getattr(config, "EMBED_FONT", "")
    if not rel:
        return ""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), rel)
    if not os.path.exists(path):
        return ""
    import base64
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    print("· police embarquee : %s (%d ko)" % (rel, len(b64) // 1024))
    return ("@font-face{font-family:'JetBrains Mono';font-style:normal;"
            "font-weight:100 800;font-display:block;"
            "src:url(data:font/woff2;base64,%s) format('woff2')}" % b64)


def footer():
    return ("dernière mise à jour : %s  ·  généré automatiquement par "
            "GitHub Actions" % datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC"))


def demo_data():
    return dict(
        uptime=uptime_label(config.FALLBACK_CREATED_AT),
        years_label="%d années" % max(
            1, datetime.utcnow().year
            - int(config.FALLBACK_CREATED_AT[:4]) + 1),
        repos=fr(28), public=fr(21), private=fr(7),
        commits=fr(1487), stars=fr(94), followers=fr(23),
        loc_total=fr(184320), loc_add=fr(147905), loc_del=fr(36415),
        languages=config.LANGUAGES_FALLBACK,
        tagline="build . solve . repeat",
        footer=footer(),
    )


def real_data():
    u = query(Q_USER, {"login": USER})["user"]
    created = u["createdAt"]
    print("· depots...")
    repos = fetch_repos(USER, u["id"])
    print("· commits...")
    commits = commits_all_time(USER, created)
    print("· lignes de code (peut prendre quelques minutes)...")
    add, dele = lines_of_code(repos, u["id"])
    langs = language_mix(repos) if config.USE_REAL_LANGUAGES else None
    stars = sum(r["stargazerCount"] for r in repos)
    pub, priv = u["pub"]["totalCount"], u["priv"]["totalCount"]
    return dict(
        uptime=uptime_label(created),
        years_label="%d années" % (datetime.utcnow().year - int(created[:4]) + 1),
        repos=fr(pub + priv), public=fr(pub), private=fr(priv),
        commits=fr(commits), stars=fr(stars),
        followers=fr(u["followers"]["totalCount"]),
        loc_total=fr(add - dele if add - dele > 0 else add),
        loc_add=fr(add), loc_del=fr(dele),
        languages=langs or config.LANGUAGES_FALLBACK,
        tagline="build . solve . repeat",
        footer=footer(),
    )


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ascii_rows = open(os.path.join(here, "ascii_portrait.txt"),
                      encoding="utf-8").read().split("\n")
    while ascii_rows and not ascii_rows[-1].strip():
        ascii_rows.pop()

    if not config.TITLE:
        config.TITLE = "%s@github" % USER.lower()

    if DEMO or not TOKEN:
        if not DEMO:
            print("! ACCESS_TOKEN absent : bascule en mode demo")
        data = demo_data()
    else:
        data = real_data()
    data["ascii"] = ascii_rows
    data["font_face"] = font_face()

    for theme in ("dark", "light"):
        svg = svg_builder.build(theme, data)
        out = os.path.join(here, "%s_mode.svg" % theme)
        with open(out, "w", encoding="utf-8") as f:
            f.write(svg)
        print("✓ %s (%d ko)" % (os.path.basename(out), len(svg) // 1024))


if __name__ == "__main__":
    main()
