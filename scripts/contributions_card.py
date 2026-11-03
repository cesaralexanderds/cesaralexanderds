"""Generate an SVG card with the user's all-time GitHub contributions.

Sums contributionCalendar.totalContributions year by year since the account
was created. Private contributions are included only when the profile has
"Include private contributions on my profile" enabled.
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

API = "https://api.github.com/graphql"


def query(token, gql, variables):
    body = json.dumps({"query": gql, "variables": variables}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


def total_contributions(token, login):
    created = query(token, "query($l:String!){user(login:$l){createdAt}}", {"l": login})
    start_year = int(created["user"]["createdAt"][:4])
    now = datetime.now(timezone.utc)
    total = 0
    for year in range(start_year, now.year + 1):
        data = query(
            token,
            "query($l:String!,$f:DateTime!,$t:DateTime!){user(login:$l){"
            "contributionsCollection(from:$f,to:$t){contributionCalendar{totalContributions}}}}",
            {"l": login, "f": f"{year}-01-01T00:00:00Z", "t": f"{year}-12-31T23:59:59Z"},
        )
        total += data["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    return total, start_year


def render(total, start_year):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="360" height="120" viewBox="0 0 360 120" role="img" aria-label="{total:,} total contributions">
  <style>
    .label {{ font: 600 14px 'Segoe UI', Ubuntu, sans-serif; fill: #c792ea; }}
    .value {{ font: 700 40px 'Segoe UI', Ubuntu, sans-serif; fill: #ffffff; }}
    .sub {{ font: 400 12px 'Segoe UI', Ubuntu, sans-serif; fill: #a6accd; }}
  </style>
  <rect width="360" height="120" rx="10" fill="#292d3e"/>
  <text x="180" y="32" text-anchor="middle" class="label">Total Contributions</text>
  <text x="180" y="78" text-anchor="middle" class="value">{total:,}</text>
  <text x="180" y="102" text-anchor="middle" class="sub">{start_year} - Present · public + private</text>
</svg>
"""


def main():
    token = os.environ["GITHUB_TOKEN"]
    login = os.environ["GITHUB_LOGIN"]
    out = sys.argv[1] if len(sys.argv) > 1 else "contributions.svg"
    total, start_year = total_contributions(token, login)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(render(total, start_year))
    print(f"{login}: {total} contributions since {start_year} -> {out}")


if __name__ == "__main__":
    main()
