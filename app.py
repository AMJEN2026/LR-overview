"""
MA Research Radar — Public Version
====================================
Reads papers from papers.json (no live API calls).
To update papers: run fetch.py locally and push papers.json to GitHub.
"""

import streamlit as st
import json
from collections import defaultdict
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="MA Research Radar",
    page_icon="📡",
    layout="wide",
)

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
    "Behavioral Research In Accounting":         "BRIA",
    "Accounting and Business Research":          "ABR",
    "Review of Accounting Studies":              "RAS",
}

# ══════════════════════════════════════════════════════════════════════
# LOAD PAPERS FROM FILE
# ══════════════════════════════════════════════════════════════════════

@st.cache_data
def load_papers():
    path = Path(__file__).parent / "papers.json"
    if not path.exists():
        return [], ""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("papers", []), data.get("fetched_at", "")

papers, fetched_at = load_papers()

# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════

def short_journal(full):
    return JOURNAL_SHORT.get(full, full[:18] if full else "?")


def fulltext_match(paper, query):
    if not query.strip():
        return True
    text = " ".join([
        paper.get("title") or "",
        paper.get("abstract") or "",
        str(paper.get("year") or ""),
        paper.get("journal") or "",
        " ".join(paper.get("authors") or []),
    ]).lower()
    return all(word in text for word in query.lower().split())

# ══════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════

st.markdown("## 📡 Management Accounting Research Radar")
if fetched_at:
    st.caption(f"Data last updated: {fetched_at}  ·  {len(papers)} papers across top MA journals")
else:
    st.error("No papers.json found. Run fetch.py locally and push the file to GitHub.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════
# SEARCH BAR
# ══════════════════════════════════════════════════════════════════════

search_query = st.text_input(
    "search",
    placeholder="🔍  Search by author, title, keyword, journal…",
    label_visibility="collapsed",
)

st.divider()

# ══════════════════════════════════════════════════════════════════════
# MAIN LAYOUT
# ══════════════════════════════════════════════════════════════════════

# Apply search
display_papers = papers
if search_query.strip():
    display_papers = [p for p in papers if fulltext_match(p, search_query)]

left_col, right_col = st.columns([1, 2], gap="large")

# ─────────────────────────────────────────────────────────────────────
# LEFT — TEMA OVERSIGT
# ─────────────────────────────────────────────────────────────────────

with left_col:
    st.markdown("### 🗂️ Themes")

    theme_counts = defaultdict(int)
    for p in display_papers:
        theme_counts[p.get("primary_theme", "Other")] += 1

    if "active_theme" not in st.session_state:
        st.session_state["active_theme"] = "All themes"

    all_active = st.session_state["active_theme"] == "All themes"
    if st.button(
        f"{'✅ ' if all_active else ''}All themes  ({len(display_papers)})",
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

    # Get filter options from data
    all_journals = sorted({p.get("journal","") for p in papers if p.get("journal")})
    all_years    = sorted({p.get("year") for p in papers if p.get("year")}, reverse=True)

    f1, f2, f3 = st.columns(3)
    with f1:
        journal_filter = st.selectbox("Journal", ["All journals"] + all_journals)
    with f2:
        year_filter = st.selectbox("Year", ["All years"] + all_years)
    with f3:
        sort_by = st.selectbox("Sort by", ["Newest first", "Oldest first", "Most cited", "Journal A–Z"])

    # Apply filters
    active_theme = st.session_state.get("active_theme", "All themes")
    filtered = display_papers

    if active_theme != "All themes":
        filtered = [p for p in filtered if p.get("primary_theme") == active_theme]
    if journal_filter != "All journals":
        filtered = [p for p in filtered if p.get("journal") == journal_filter]
    if year_filter != "All years":
        filtered = [p for p in filtered if p.get("year") == year_filter]

    # Sort
    if sort_by == "Newest first":
        filtered = sorted(filtered, key=lambda p: (p.get("date") or str(p.get("year",""))), reverse=True)
    elif sort_by == "Oldest first":
        filtered = sorted(filtered, key=lambda p: (p.get("date") or str(p.get("year",""))))
    elif sort_by == "Most cited":
        filtered = sorted(filtered, key=lambda p: p.get("cited_by_count", 0), reverse=True)
    elif sort_by == "Journal A–Z":
        filtered = sorted(filtered, key=lambda p: p.get("journal", ""))

    st.caption(f"Showing **{len(filtered)}** of {len(display_papers)} papers")

    if not filtered:
        st.info("No papers match the current filters.")
    else:
        for paper in filtered:
            title     = paper.get("title") or "Untitled"
            doi       = paper.get("doi", "")
            year_p    = paper.get("year", "?")
            journal   = paper.get("journal", "")
            authors   = ", ".join((paper.get("authors") or [])[:3])
            cited     = paper.get("cited_by_count", 0)
            oa        = paper.get("open_access", False)
            abstract  = paper.get("abstract", "")
            primary   = paper.get("primary_theme", "")
            secondary = paper.get("secondary_themes", [])

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
                        st.link_button("🔗 Open paper", doi)
