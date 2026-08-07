"""
MA Radar — Paper Fetcher
=========================
Run this script on your own computer whenever you want to update the papers.
It fetches from OpenAlex and saves the results to papers.json.

After running, push papers.json to GitHub — the public app will update automatically.

Run with:  py fetch.py
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════
# CONFIGURATION — edit these as needed
# ══════════════════════════════════════════════════════════════════════

API_KEY = "0RwxKibyjeBOuDBPRF5dH8"

JOURNALS = {
    "Management Accounting Research":            "1044-5005",
    "Accounting, Organizations and Society":     "0361-3682",
    "Journal of Accounting Research":            "0021-8456",
    "The Accounting Review":                     "0001-4826",
    "Contemporary Accounting Research":          "0823-9150",
    "European Accounting Review":                "0963-8180",
    "Critical Perspectives on Accounting":       "1045-2354",
    "Journal of Management Accounting Research": "1049-2127",
    "Accounting, Auditing & Accountability Journal": "1758-4205",
    "Behavioral Research In Accounting":         "1558-8009",
    "Accounting and Business Research":          "2159-4260",
    "Review of Accounting Studies":              "1573-7136",
}

YEARS = [2024, 2025, 2026]   # which years to fetch
MAX_PER_JOURNAL = 50         # max papers per journal per year

THEMES = {
    "Budgeting":               ["budget", "forecast", "appropriation"],
    "Performance measurement": ["performance measurement", "balanced scorecard",
                                "kpi", "performance indicator", "performance evaluation"],
    "Costing":                 ["cost accounting", "overhead", "activity-based",
                                "target costing", "standard costing", "cost allocation"],
    "Management control":      ["management control", "control system", "accountability",
                                "internal control", "management information"],
    "Strategy":                ["strateg", "competitive advantage", "strategic management",
                                "business model"],
    "Sustainability / ESG":    ["esg", "carbon", "environmental accounting",
                                "social accounting", "integrated reporting", "climate change",
                                "greenhouse", "net zero"],
    "Digital & AI":            ["digital", "artificial intelligence", "machine learning",
                                "algorithm", "erp", "information system", "automation",
                                "big data", "analytics"],
    "Governance":              ["governance", "board", "audit committee",
                                "executive compensation", "agency"],
    "Behavioural":             ["behaviour", "behavior", "psychology", "bias",
                                "cognitive", "decision-making", "judgment"],
    "Crisis & Uncertainty":    ["crisis", "uncertainty", "covid", "pandemic",
                                "disruption", "risk", "volatility"],
    "Public sector":           ["public sector", "government", "ngo", "non-profit",
                                "municipality", "healthcare", "hospital"],
}

# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

def reconstruct_abstract(inv):
    if not inv:
        return ""
    pos = []
    for word, locs in inv.items():
        for loc in locs:
            while len(pos) <= loc:
                pos.append("")
            pos[loc] = word
    return " ".join(pos)


def assign_themes(title, abstract):
    text = (title + " " + abstract).lower()
    matched = [lbl for lbl, kws in THEMES.items() if any(kw in text for kw in kws)]
    if not matched:
        return "Other", []
    return matched[0], matched[1:]


# ══════════════════════════════════════════════════════════════════════
# FETCH
# ══════════════════════════════════════════════════════════════════════

fields = (
    "id,title,doi,publication_year,publication_date,"
    "primary_location,authorships,abstract_inverted_index,"
    "open_access,cited_by_count"
)

all_papers = []
seen_ids   = set()

for year in YEARS:
    print(f"\nFetching year {year}...")
    for journal_name, issn in JOURNALS.items():
        print(f"  {journal_name}...", end=" ")
        params = {
            "filter":   f"primary_location.source.issn:{issn},publication_year:{year}",
            "sort":     "publication_date:desc",
            "per-page": MAX_PER_JOURNAL,
            "select":   fields,
            "api_key":  API_KEY,
        }
        try:
            r = requests.get(
                "https://api.openalex.org/works",
                params=params,
                timeout=30,
            )
            r.raise_for_status()
            results = r.json().get("results", [])
            count = 0
            for p in results:
                pid = p.get("id", "")
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)
                abstract = reconstruct_abstract(p.get("abstract_inverted_index"))
                title    = p.get("title") or ""
                primary, secondary = assign_themes(title, abstract)
                authors  = [
                    a.get("author", {}).get("display_name", "")
                    for a in (p.get("authorships") or [])[:5]
                ]
                all_papers.append({
                    "id":               pid,
                    "title":            title,
                    "doi":              p.get("doi", ""),
                    "year":             p.get("publication_year"),
                    "date":             p.get("publication_date", ""),
                    "journal":          (p.get("primary_location") or {}).get("source", {}).get("display_name", ""),
                    "authors":          authors,
                    "abstract":         abstract,
                    "primary_theme":    primary,
                    "secondary_themes": secondary,
                    "open_access":      (p.get("open_access") or {}).get("is_oa", False),
                    "cited_by_count":   p.get("cited_by_count", 0),
                })
                count += 1
            print(f"{count} papers")
            time.sleep(1)   # be polite to OpenAlex
        except Exception as e:
            print(f"ERROR: {e}")
            time.sleep(3)

# ══════════════════════════════════════════════════════════════════════
# SAVE
# ══════════════════════════════════════════════════════════════════════

output = {
    "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "total":      len(all_papers),
    "papers":     all_papers,
}

out_path = Path(__file__).parent / "papers.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n✅ Done! {len(all_papers)} papers saved to papers.json")
print("Now push papers.json to GitHub to update the public app.")
