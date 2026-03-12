"""
HTML rendering helpers for the Linguistic Misinformation Markers app.
"""

import re

BAR_COLORS = {
    "ALL_CAPS":          "#e67e22",
    "EXCLAMATION_MARKS": "#c0392b",
    "HEDGING":           "#27ae60",
    "ADJECTIVES":        "#2980b9",
    "UNK":               "#8e44ad",
}

TAG_CSS = {
    "ALL_CAPS":          "hl-orange",
    "EXCLAMATION_MARKS": "hl-red",
    "HEDGING":           "hl-green",
    "ADJECTIVES":        "hl-blue",
    "UNK":               "hl-purple",
}

# Light background tints used when ALL_CAPS overlaps with another tag
TAG_BG = {
    "EXCLAMATION_MARKS": "#fcd6d6",
    "HEDGING":           "#d4edda",
    "ADJECTIVES":        "#cce5ff",
    "UNK":               "#e2d4f0",
}


def compute_highlights(text: str, active_tag: str, tag_words: dict) -> str:
    """Highlight words in text based on the active tag button.

    tag_words maps tag name → list of matched strings from the annotation data.
    When active_tag is 'ALL', all tags are highlighted; otherwise only the selected tag.
    When ALL_CAPS overlaps with another tag, the word gets an orange underline plus the
    other tag's text color.
    """
    tags_to_apply = list(TAG_CSS.keys()) if active_tag == "ALL" else [active_tag]

    # Collect all tags that apply to each (start, end) span
    span_tags: dict = {}
    for tag in tags_to_apply:
        for word in tag_words.get(tag, []):
            if not word:
                continue
            for m in re.finditer(re.escape(word), text):
                key = (m.start(), m.end())
                span_tags.setdefault(key, []).append(tag)

    result = ""
    pos = 0
    for (start, end) in sorted(span_tags):
        if start < pos:
            continue
        word = text[start:end]
        tags = span_tags[(start, end)]

        if "ALL_CAPS" in tags and len(tags) > 1:
            other_tag = next(t for t in tags if t != "ALL_CAPS")
            bg = TAG_BG.get(other_tag, "#fff3e0")
            span = (
                f'<span style="background:{bg}; color:#e67e22; '
                f'font-weight:700; text-transform:uppercase; border-radius:3px; padding:0 2px;">{word}</span>'
            )
        else:
            span = f'<span class="{TAG_CSS[tags[0]]}">{word}</span>'

        result += text[pos:start] + span
        pos = end
    result += text[pos:]
    return result


def render_card(entry: dict, active_tag: str = "ALL") -> str:
    """Build the HTML for one result card."""
    text = compute_highlights(entry["text"], active_tag, entry.get("tag_words", {}))

    tag_html = "".join(
        f'<span class="tag-pill tag-{t}">{t}</span>'
        for t in entry["tags"]
    )

    return f"""
    <div class="result-card">
        <div class="result-id">{entry['id']}</div>
        <div class="result-text">{text}</div>
        <div class="tag-container">{tag_html}</div>
    </div>
    """


def render_bar_chart(tag_counts: dict) -> str:
    """Build an HTML/CSS horizontal bar chart for tag frequencies.

    Bars are scaled relative to the highest tag count. Gridlines at 25/50/75/100%
    provide a true-zero visual anchor.
    """
    max_val = max(max(tag_counts.values(), default=0), 1)

    # Gridlines overlay (25%, 50%, 75%, 100%)
    gridlines = "".join(
        f'<div style="position:absolute; left:{pct}%; top:0; bottom:0; '
        f'width:1px; background:rgba(0,0,0,0.08);"></div>'
        for pct in (25, 50, 75, 100)
    )
    # Tick labels below the grid
    tick_labels = "".join(
        f'<div style="position:absolute; left:{pct}%; transform:translateX(-50%); '
        f'font-family:\'JetBrains Mono\',monospace; font-size:0.6rem; color:#bbb;">{pct}%</div>'
        for pct in (0, 25, 50, 75, 100)
    )

    rows = ""
    for tag, count in tag_counts.items():
        pct = (count / max_val) * 100
        color = BAR_COLORS.get(tag, "#aaa")
        rows += (
            f'<div style="display:flex; align-items:center; margin-bottom:10px;">'
            f'<div style="width:160px; text-align:right; padding-right:12px; font-family:\'JetBrains Mono\',monospace; font-size:0.7rem; color:#666;">{tag}</div>'
            f'<div style="flex:1; background:#f0f0f0; border-radius:3px; height:22px; position:relative;">'
            f'{gridlines}'
            f'<div style="width:{pct}%; background:{color}; height:100%; border-radius:3px; display:flex; align-items:center; padding-left:8px; position:relative; z-index:1;">'
            f'<span style="font-family:\'JetBrains Mono\',monospace; font-size:0.72rem; color:white; font-weight:700;">{count}</span>'
            f'</div></div></div>'
        )

    return (
        f'<div style="padding:12px 0;">'
        f'<div style="display:flex; margin-left:160px; position:relative; height:14px; margin-bottom:4px;">{tick_labels}</div>'
        f'{rows}'
        f'</div>'
    )
