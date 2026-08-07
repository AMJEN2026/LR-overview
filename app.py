"""
Management Accounting Research Radar — Public Version
======================================================
A simple public dashboard for browsing recent MA journal papers.
No stars, no API key, no AI summaries.
Hosted on Streamlit Community Cloud.

Run with:  streamlit run app.py
"""

import streamlit as st
import requests
import time
from collections import defaultdict

# ══════════════════════════════════════════════════════════════════════
# STATIC DATA
# ══════════════════════════════════════════════════════════════════════

JOURNALS = {
    "All top journals":                          None,
    "Management Accounting Research":            "1044-5005",
    "Accounting, Organizations and Society":     "0361-3682",
    "Journal of Accounting Research":            "0021-8456",
    "The Accounting Review":                     "0001-4826",
    "Contemporary Accounting Research":          "0823-9150",
    "European Accounting Review":                "0963-8180",
    "Critical Perspectives on Accounting":       "1045-2354",
    "Journal of Management Accounting Research": "1049-2127",
"Accounting, Auditing & Accountability Journal": "1758-4205",
"Behavioral Research In Accounting": "1558-8009",
"Accounting and Business Research": "2159-4260",
"Review of Accounting Studies": "1573-7136",
   
}

JOURNAL_SHORT = {
    "Management Accounting Research":            "MAR",
    "Accounting, Organizations and Society":     "AOS",
    "Journal of Accounting Research":            "JAR",
    "The Accounting Review":                     "TAR",
    "Contemporary Accounting Research":          "CAR",
    "European Accounting Review":                "EAR",
    "Critical Perspectives on Accounting":       "CPA",
    "Journal of Management Accounting Research": "JMAR",
    "Accounting, Auditing & Accountability Journal": "AAAJ", 
"Behavioral Research In Accounting": "BRIA",
"Accounting and Business Research": "ABR",
"Review of Accounting Studies": "RAS",
    
}

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
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="MA Research Radar",
    page_icon="📡",
    layout="wide",
)

# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

def reconstruct_abstract(inv: dict | None) -> str:
    if not inv:
        return ""
    pos: list[str] = []
    for word, locs in inv.items():
        for loc in locs:
            while len(pos) <= loc:
                pos.append("")
            pos[loc] = word
    return " ".join(pos)


def assign_themes(title: str, abstract: str) -> tuple[str, list[str]]:
    text    = (title + " " + abstract).lower()
    matched = [lbl for lbl, kws in THEMES.items() if any(kw in text for kw in kws)]
    if not matched:
        return "Other", []
    return matched[0], matched[1:]


def short_journal(full: str) -> str:
    return JOURNAL_SHORT.get(full, full[:18] if full else "?")


def enrich(paper: dict) -> dict:
    abstract = reconstruct_abstract(paper.get("abstract_inverted_index"))
    title    = paper.get("title") or ""
    primary, secondary = assign_themes(title, abstract)
    paper["_abstract"]  = abstract
    paper["_primary"]   = primary
    paper["_secondary"] = secondary
    return paper


def fetch_papers(issns: list[str], year: int, max_per: int) -> list[dict]:
    papers = []
    fields = (
        "id,title,doi,publication_year,publication_date,"
        "primary_location,authorships,abstract_inverted_index,"
        "open_access,cited_by_count"
    )
    # Combine all ISSNs into one request using | (or)
    issn_filter = "|".join(f"primary_location.source.issn:{issn}" for issn in issns)
    params = {
        "filter":   f"{issn_filter},publication_year:{year}",
        "sort":     "publication_date:desc",
        "per-page": max_per,
        "select":   fields,
        "api_key":  "0RwxKibyjeBOuDBPRF5dH8",
    }
    try:
        r = requests.get("https://api.openalex.org/works", params=params, timeout=30)
        r.raise_for_status()
        for p in r.json().get("results", []):
            papers.append(enrich(p))
    except Exception as e:
        st.error(f"Could not fetch papers: {e}")
    return papers


def fulltext_match(paper: dict, query: str) -> bool:
    if not query.strip():
        return True
    text = " ".join([
        paper.get("title") or "",
        paper.get("_abstract") or "",
        str(paper.get("publication_year") or ""),
        (paper.get("primary_location") or {}).get("source", {}).get("display_name", ""),
        " ".join(
            a.get("author", {}).get("display_name", "")
            for a in (paper.get("authorships") or [])
        ),
    ]).lower()
    return all(word in text for word in query.lower().split())


# ══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    journal_scope = st.selectbox("Journal", list(JOURNALS.keys()))
    year          = st.selectbox("Year", [2026, 2025, 2024, 2023], index=1)
    max_per       = st.slider("Max papers per journal", 5, 50, 20, 5)
    fetch_btn     = st.button("🔄 Load papers", use_container_width=True, type="primary")

    st.divider()
    st.caption(
        "Papers fetched from [OpenAlex](https://openalex.org) (free, open data).\n\n"
        "Themes are assigned automatically based on title and abstract keywords."
    )

# ══════════════════════════════════════════════════════════════════════
# FETCH
# ══════════════════════════════════════════════════════════════════════

if fetch_btn:
    issns = (
        [v for v in JOURNALS.values() if v]
        if journal_scope == "All top journals"
        else [JOURNALS[journal_scope]]
    )
    with st.spinner("Fetching papers from OpenAlex…"):
        papers = fetch_papers(issns, year, max_per)
    st.session_state["papers"] = papers

# ══════════════════════════════════════════════════════════════════════
# HEADER + SEARCH
# ══════════════════════════════════════════════════════════════════════

st.markdown("## 📡 Management Accounting Research Radar")
st.caption("Browse recent papers from top management accounting journals.")

search_query = st.text_input(
    "search",
    placeholder="🔍  Search by author, title, keyword, journal…",
    label_visibility="collapsed",
)

st.divider()

# ══════════════════════════════════════════════════════════════════════
# MAIN LAYOUT
# ══════════════════════════════════════════════════════════════════════

if "papers" not in st.session_state:
    st.info("👈 Choose a journal and year in the sidebar, then click **Load papers**.")
    st.stop()

papers = st.session_state["papers"]

# Apply search filter
display_papers = papers
if search_query.strip():
    display_papers = [p for p in papers if fulltext_match(p, search_query)]

left_col, right_col = st.columns([1, 2], gap="large")

# ─────────────────────────────────────────────────────────────────────
# LEFT — TEMA OVERSIGT
# ─────────────────────────────────────────────────────────────────────

with left_col:
    st.markdown("### 🗂️ Themes overview")

    theme_counts: dict[str, int] = defaultdict(int)
    for p in papers:
        theme_counts[p.get("_primary", "Other")] += 1

    if "active_theme" not in st.session_state:
        st.session_state["active_theme"] = "All themes"

    all_active = st.session_state["active_theme"] == "All themes"
    if st.button(
        f"{'✅ ' if all_active else ''}All themes  ({sum(theme_counts.values())})",
        use_container_width=True,
        type="primary" if all_active else "secondary",
    ):
        st.session_state["active_theme"] = "All themes"
        st.rerun()

    for theme, count in sorted(theme_counts.items(), key=lambda x: -x[1]):
        active = st.session_state["active_theme"] == theme
        if st.button(
            f"{'✅ ' if active else ''}{theme}  ({count})",
            use_container_width=True,
            type="primary" if active else "secondary",
        ):
            st.session_state["active_theme"] = theme
            st.rerun()

# ─────────────────────────────────────────────────────────────────────
# RIGHT — PAPER LIST
# ─────────────────────────────────────────────────────────────────────

with right_col:
    st.markdown("### 📄 Papers")

    f1, f2 = st.columns(2)
    with f1:
        journal_filter = st.selectbox(
            "Filter by journal",
            ["All journals"] + [k for k in JOURNALS if k != "All top journals"],
        )
    with f2:
        sort_by = st.selectbox(
            "Sort by",
            ["Newest first", "Oldest first", "Most cited", "Journal A–Z"],
        )

    # Apply filters
    active_theme = st.session_state.get("active_theme", "All themes")
    filtered = display_papers

    if active_theme != "All themes":
        filtered = [p for p in filtered if p.get("_primary") == active_theme]

    if journal_filter != "All journals":
        filtered = [
            p for p in filtered
            if (p.get("primary_location") or {}).get("source", {}).get("display_name", "") == journal_filter
        ]

    # Sort
    if sort_by == "Newest first":
        filtered = sorted(filtered, key=lambda p: p.get("publication_date", "") or str(p.get("publication_year", "")), reverse=True)
    elif sort_by == "Oldest first":
        filtered = sorted(filtered, key=lambda p: p.get("publication_date", "") or str(p.get("publication_year", "")))
    elif sort_by == "Most cited":
        filtered = sorted(filtered, key=lambda p: p.get("cited_by_count", 0), reverse=True)
    elif sort_by == "Journal A–Z":
        filtered = sorted(filtered, key=lambda p:
            (p.get("primary_location") or {}).get("source", {}).get("display_name", ""))

    st.caption(f"Showing **{len(filtered)}** of {len(papers)} papers")

    if not filtered:
        st.info("No papers match the current filters.")
    else:
        for paper in filtered:
            title    = paper.get("title") or "Untitled"
            doi      = paper.get("doi", "")
            year_p   = paper.get("publication_year", "?")
            journal  = (paper.get("primary_location") or {}).get("source", {}).get("display_name", "")
            authors  = ", ".join(
                a.get("author", {}).get("display_name", "")
                for a in (paper.get("authorships") or [])[:3]
            )
            cited    = paper.get("cited_by_count", 0)
            oa       = (paper.get("open_access") or {}).get("is_oa", False)
            abstract = paper.get("_abstract", "")
            primary  = paper.get("_primary", "")
            secondary= paper.get("_secondary", [])

            with st.container(border=True):
                st.markdown(f"**{title}**")

                meta = []
                if authors: meta.append(authors)
                if journal: meta.append(f"*{short_journal(journal)}*")
                if year_p:  meta.append(str(year_p))
                if cited:   meta.append(f"📚 {cited}")
                if oa:      meta.append("🔓 Open access")
                st.caption("  ·  ".join(meta))

                badges = []
                if primary and primary != "Other":
                    badges.append(f"🎯 {primary}")
                for s in secondary[:2]:
                    badges.append(f"↳ {s}")
                if badges:
                    st.caption("  ".join(badges))

                with st.expander("Abstract & details"):
                    if abstract:
                        st.write(abstract)
                    else:
                        st.caption("No abstract available.")
                    if doi:
                        st.link_button("🔗 Open paper", doi, use_container_width=False)
