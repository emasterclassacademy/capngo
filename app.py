import os
import streamlit as st
import subprocess
from playwright.sync_api import sync_playwright

# Ensure Playwright browsers are installed
if not os.path.exists(os.path.expanduser("~/.cache/ms-playwright")):
    subprocess.run(["playwright", "install", "chromium"], check=True)

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import json
import re
import tempfile
import streamlit.components.v1 as components
from pycaps import CapsPipelineBuilder, LimitByCharsSplitter, SubtitleLayoutOptions
from pycaps.layout.definitions import VerticalAlignment, VerticalAlignmentType

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Cap'n'Go", page_icon="🎬", layout="wide")

# ─── GLOBAL CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── FIX 4: Hide Streamlit top toolbar/header when hosted ── */
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stHeader"],
header[data-testid="stHeader"] { display: none !important; }

:root {
    --bg:       #09090f;
    --surface:  #111118;
    --surface2: #16161e;
    --surface3: #1c1c26;
    --border:   #23232f;
    --border2:  #2e2e3d;
    --accent:   #00ff41;
    --text:     #e8e8f0;
    --muted:    #5a5a72;
    --danger:   #ff3b5c;
    --radius:   10px;
}

*, *::before, *::after { box-sizing: border-box; }
a { text-decoration: none !important; color: inherit !important; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="block-container"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Syne', sans-serif !important;
}
[data-testid="block-container"] { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none !important; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 4px; }

.stMarkdown p, label,
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label {
    color: var(--text) !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 0.82rem !important;
}
.stCaption { color: var(--muted) !important; font-size: 0.72rem !important; }
strong { color: var(--text) !important; }

.panel-title {
    font-size: 0.6rem; font-weight: 700; letter-spacing: 0.2em;
    text-transform: uppercase; color: var(--muted);
    display: flex; align-items: center; gap: 10px;
}
.panel-title::after { content: ''; flex: 1; height: 1px; background: var(--border); }

.section-label {
    font-size: 0.78rem; font-weight: 700; color: var(--text);
    font-family: 'Syne', sans-serif;
    display: block; margin: 4px 0 4px 0 !important;
}

textarea, [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
    background: var(--surface2) !important;
    border: 1px solid var(--border2) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
}
textarea:focus, [data-baseweb="input"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(0,255,65,0.08) !important;
    outline: none !important;
}

[data-baseweb="select"] > div {
    background: var(--surface2) !important;
    border: 1px solid var(--border2) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
}
[data-baseweb="select"] span,
[data-baseweb="select"] div { color: var(--text) !important; background: transparent !important; }

body [data-baseweb="popover"],
body [data-baseweb="popover"] > div,
body [class*="menu"] {
    background: #16161e !important; border: 1px solid #2e2e3d !important;
    border-radius: 10px !important; box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important;
    overflow: hidden !important;
}
body ul[data-baseweb="menu"], body [data-baseweb="menu"] {
    background: #16161e !important; border: none !important;
    padding: 0 !important; margin: 0 !important;
}
body [data-baseweb="menu"] li,
body [data-baseweb="menu"] [role="option"],
body [role="option"] {
    background: #16161e !important; color: #e8e8f0 !important;
    font-size: 0.8rem !important; font-family: 'Syne', sans-serif !important;
    padding: 9px 14px !important; border: none !important;
    border-bottom: 1px solid #23232f !important; margin: 0 !important; cursor: pointer !important;
}
body [data-baseweb="menu"] li:last-child,
body [data-baseweb="menu"] [role="option"]:last-child { border-bottom: none !important; }
body [data-baseweb="menu"] li:hover,
body [data-baseweb="menu"] [role="option"]:hover,
body [data-baseweb="menu"] li[aria-selected="true"] { background: #1c1c26 !important; color: #e8e8f0 !important; }

/* ── Widget spacing ── */
[data-testid="stFileUploader"] { margin-top: 4px !important; margin-bottom: 4px !important; }
[data-testid="stSelectbox"]    { margin-top: 4px !important; margin-bottom: 4px !important; }
[data-testid="stTextArea"]     { margin-top: 4px !important; margin-bottom: 4px !important; }
[data-testid="stTextInput"]    { margin-top: 4px !important; margin-bottom: 4px !important; }
[data-testid="stCheckbox"]     { margin-top: 4px !important; margin-bottom: 4px !important; }
[data-testid="stSlider"]       { margin-top: 4px !important; margin-bottom: 4px !important; }
[data-testid="stRadio"]        { margin-top: 0px !important; margin-bottom: 0px !important; }
[data-testid="stButton"]       { margin-top: 4px !important; margin-bottom: 4px !important; }
[data-testid="stColorPicker"]  { margin-top: 4px !important; margin-bottom: 4px !important; }

.panel-title { margin: 0 !important; }
.adv-heading { margin: 0px 0 0px 0 !important; }

[role="radiogroup"] label,
[role="radiogroup"] span { color: var(--text) !important; font-size: 0.8rem !important; }
[data-testid="stRadio"] p,
[data-testid="stRadio"] span { color: white !important; }

/* Hide radio widget label */
div[data-testid="stRadio"] > label,
div[data-testid="stRadio"] [data-testid="stWidgetLabel"] {
    display: none !important; height: 0 !important;
    margin: 0 !important; padding: 0 !important;
}
/* Title radio row sizing — scoped by key name */
[data-testid="stRadio"]:has(div[role="radiogroup"] input[name="title_radio_widget"]) label {
    height: 38px !important; display: flex !important;
    align-items: center !important; margin: 0 !important; padding: 0 !important;
}
[data-testid="stRadio"]:has(div[role="radiogroup"] input[name="title_radio_widget"]) div[role="radiogroup"] {
    gap: 4px !important; display: flex !important; flex-direction: column !important;
}

[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
    background: var(--accent) !important; border-color: var(--accent) !important;
}
[data-testid="stSlider"] p,
[data-testid="stSlider"] span { color: var(--text) !important; font-size: 0.78rem !important; }

.stButton > button {
    background: var(--surface2) !important; border: 1px solid var(--border2) !important;
    color: var(--text) !important; border-radius: var(--radius) !important;
    font-family: 'Syne', sans-serif !important; font-weight: 600 !important;
    font-size: 0.82rem !important; transition: all 0.18s ease !important;
    padding: 0.5rem 1rem !important;
}
.stButton > button:hover { background: var(--surface3) !important; }
.stButton > button[kind="primary"] {
    background: rgba(0,255,65,0.08) !important; border: 1.5px solid var(--accent) !important;
    color: var(--accent) !important; box-shadow: 0 0 16px rgba(0,255,65,0.12) !important;
}
.stButton > button[kind="primary"]:hover {
    background: rgba(0,255,65,0.14) !important; box-shadow: 0 0 26px rgba(0,255,65,0.2) !important;
}
.stButton > button:disabled { opacity: 0.35 !important; }

/* ── Template buttons ── */
.stButton > button {
    height: 50px; border-radius: 12px;
    font-size: 0.75rem; letter-spacing: 0.08em; text-transform: uppercase;
}

[data-testid="stExpander"] {
    background: var(--surface2) !important; border: 1px solid var(--border2) !important;
    border-radius: var(--radius) !important; overflow: hidden !important;
}
[data-testid="stExpander"] > details > summary {
    background: var(--surface2) !important; padding: 10px 14px !important;
    list-style: none !important; cursor: pointer !important;
}
[data-testid="stExpander"] > details > summary::-webkit-details-marker { display: none !important; }
[data-testid="stExpander"] > details > summary::marker { display: none !important; }
[data-testid="stExpander"] > details > summary svg { display: none !important; }
[data-testid="stExpander"] > details > summary p {
    color: var(--muted) !important; font-size: 0.72rem !important;
    font-family: 'Syne', sans-serif !important; font-weight: 600 !important;
    letter-spacing: 0.06em !important; text-transform: uppercase !important;
    margin: 0 !important; background: transparent !important;
}
[data-testid="stExpander"] > details > summary:hover p { color: var(--text) !important; }
[data-testid="stExpander"] > details > div {
    background: var(--surface2) !important; padding: 14px 14px 16px !important;
    border-top: 1px solid var(--border) !important;
}
[data-testid="stExpander"] label,
[data-testid="stExpander"] [data-testid="stWidgetLabel"] p,
[data-testid="stExpander"] [data-testid="stWidgetLabel"] label {
    color: var(--text) !important; font-family: 'Syne', sans-serif !important; font-size: 0.78rem !important;
}
[data-testid="stExpander"] small { color: var(--muted) !important; }
[data-testid="stExpander"] [data-baseweb="slider"] div[role="slider"] {
    background: var(--accent) !important; border-color: var(--accent) !important;
}
[data-testid="stExpander"] [data-baseweb="select"] > div {
    background: var(--surface3) !important; border-color: var(--border2) !important; color: var(--text) !important;
}
[data-testid="stExpander"] [data-testid="stCheckbox"] label { color: var(--text) !important; }
[data-testid="stExpander"] [data-testid="stColorPicker"] > div > div {
    border: 1px solid var(--border2) !important; border-radius: 6px !important;
}

[data-testid="stTabs"] [role="tablist"] { border-bottom: 1px solid var(--border) !important; }
[data-testid="stTabs"] button[role="tab"] {
    background: transparent !important; color: var(--muted) !important;
    border: none !important; border-bottom: 2px solid transparent !important;
    font-family: 'Syne', sans-serif !important; font-size: 0.72rem !important;
    font-weight: 600 !important; padding: 8px 14px !important;
    border-radius: 0 !important; transition: all 0.18s !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--text) !important; border-bottom-color: var(--accent) !important;
}
[data-testid="stTabs"] [role="tabpanel"] { background: transparent !important; padding-top: 14px !important; }

hr { border-color: var(--border) !important; margin: 16px 0 !important; }

[data-testid="stDownloadButton"] > button {
    background: rgba(0,255,65,0.08) !important; border: 1.5px solid var(--accent) !important;
    color: var(--accent) !important; border-radius: var(--radius) !important;
    font-family: 'Syne', sans-serif !important; font-weight: 700 !important; font-size: 0.82rem !important;
    height: 50px;
}
[data-testid="stDownloadButton"] > button:hover {
    background: rgba(0,255,65,0.14) !important; box-shadow: 0 0 24px rgba(0,255,65,0.18) !important;
}

[data-testid="stFileUploader"] section {
    background: var(--surface2) !important; border: 1px dashed var(--border2) !important;
    border-radius: var(--radius) !important; padding: 14px 16px !important; transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"] section:hover {
    border-color: var(--accent) !important; background: rgba(0,255,65,0.02) !important;
}
[data-testid="stFileUploadDropzone"] * {
    color: var(--muted) !important; font-family: 'Syne', sans-serif !important; font-size: 0.74rem !important;
}
[data-testid="stFileUploader"] section button {
    background: var(--surface3) !important; border: 1px solid var(--border2) !important;
    color: var(--text) !important; border-radius: 6px !important;
    font-size: 0.72rem !important; font-weight: 600 !important;
}
[data-testid="stFileUploader"] section button:hover {
    border-color: var(--accent) !important; color: var(--accent) !important;
}
[data-testid="stFileUploaderFile"] {
    background: var(--surface3) !important; border: 1px solid var(--border2) !important; border-radius: 8px !important;
}
[data-testid="stFileUploaderFileData"] span,
[data-testid="stFileUploaderFileData"] p { color: var(--text) !important; }
[data-testid="stFileUploaderFileData"] small { color: var(--muted) !important; }
[data-testid="baseButton-minimal"] { color: var(--muted) !important; background: transparent !important; }
[data-testid="baseButton-minimal"]:hover { color: var(--danger) !important; }
[data-testid="stFileUploader"] [role="progressbar"] > div { background: var(--accent) !important; }

[data-testid="stAlert"] {
    border-radius: var(--radius) !important; border-width: 1px !important;
    font-family: 'Syne', sans-serif !important; font-size: 0.78rem !important;
}
[data-testid="stVideo"] video {
    border-radius: 12px !important; border: 1px solid var(--border2) !important;
}
[data-testid="stCheckbox"] label { color: var(--text) !important; }

/* ── Placeholders & loaders ── */
.output-placeholder {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; gap: 12px; height: 280px;
    background: var(--surface2); border: 1px dashed var(--border2);
    border-radius: 14px; color: var(--muted); font-size: 0.8rem;
    font-family: 'Syne', sans-serif;
}
.loading-box {
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; gap: 14px; height: 280px;
    background: var(--surface2); border: 1px solid var(--border); border-radius: 14px;
}
.spinner {
    width: 34px; height: 34px; border: 2.5px solid var(--border2);
    border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.loading-label {
    color: var(--muted); font-size: 0.66rem; font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.14em; text-transform: uppercase;
}

/* ── Pills ── */
.pill { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.68rem; font-weight: 600; font-family: 'JetBrains Mono', monospace; }
.pill-green { background: rgba(0,255,65,0.1);  color: #00ff41; border: 1px solid rgba(0,255,65,0.25); }
.pill-blue  { background: rgba(0,200,255,0.1); color: #00c8ff; border: 1px solid rgba(0,200,255,0.25); }

.adv-heading {
    font-size: 0.62rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase;
    color: #5a5a72; margin: 12px 0 6px 0; font-family: 'Syne', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# Dropdown dark theme — portal-level injection
st.markdown("""
<style>
[data-baseweb="popover"] { background: #16161e !important; }
[data-baseweb="popover"] > div { background: #16161e !important; border: 1px solid #2e2e3d !important; border-radius: 10px !important; overflow: hidden !important; box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important; }
[data-baseweb="menu"] { background: #16161e !important; border: none !important; padding: 0 !important; }
[data-baseweb="menu"] li { background: #16161e !important; color: #e8e8f0 !important; font-family: 'Syne',sans-serif !important; font-size: 0.8rem !important; padding: 9px 14px !important; border: none !important; border-bottom: 1px solid #23232f !important; margin: 0 !important; }
[data-baseweb="menu"] li:last-child { border-bottom: none !important; }
[data-baseweb="menu"] li:hover, [data-baseweb="menu"] li[aria-selected="true"] { background: #1c1c26 !important; color: #e8e8f0 !important; }
[data-baseweb="menu"] li * { color: #e8e8f0 !important; background: transparent !important; }
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
MAX_DURATION_SECONDS = 90

# ─── CAPTION TEMPLATES ────────────────────────────────────────────────────────
TEMPLATES = {
    "karaoke": dict(
        inactive_color="#777777", active_color="#FFFC00", highlight_color="#FFFC00",
        style_choice=2, font_size=16, font_weight=900, max_words_per_chunk=3, max_lines=1,
        vertical_align="center", vertical_offset=0.2, max_width_pct=0.7, stroke_size=2,
        active_scale=1.15, drop_shadow=True, text_transform="uppercase",
        font_family="'Arial Black', Impact, sans-serif"),
    "highlighter": dict(
        inactive_color="#DDDDDD", active_color="#000000", highlight_color="#FFFC00",
        style_choice=1, font_size=16, font_weight=900, max_words_per_chunk=3, max_lines=1,
        vertical_align="center", vertical_offset=0.2, max_width_pct=0.70, stroke_size=2,
        active_scale=1.15, drop_shadow=True, text_transform="uppercase",
        font_family="'Arial Black', Impact, sans-serif"),
    "glow": dict(
        inactive_color="#666666", active_color="#FFFFFF", highlight_color="#00FF41",
        style_choice=3, font_size=16, font_weight=700, max_words_per_chunk=3, max_lines=1,
        vertical_align="center", vertical_offset=0.2, max_width_pct=0.70, stroke_size=1,
        active_scale=1.15, drop_shadow=False, text_transform="uppercase",
        font_family="'Arial Black', Impact, sans-serif"),
    "simple": dict(
        inactive_color="#888888", active_color="#FFFFFF", highlight_color="#FFFFFF",
        style_choice=2, font_size=16, font_weight=400, max_words_per_chunk=3, max_lines=1,
        vertical_align="center", vertical_offset=0.2, max_width_pct=0.70, stroke_size=0,
        active_scale=1.15, drop_shadow=False, text_transform="none",
        font_family="'Helvetica Neue', Arial, sans-serif"),
}

# ─── SESSION STATE ────────────────────────────────────────────────────────────
defaults = {
    "selected_template":      "karaoke",
    "caption_text":           "",
    "script_mode":            "default",
    "output_video_bytes":     None,
    "is_generating":          False,
    "uploaded_video_prev":    None,
    "generate_clicked":       False,
    "suggested_titles":       [],
    "generated_description":  "",
    "selected_title_idx":     0,
    "titles_generated":       False,
    # Advanced setting defaults (populated on first load / template switch)
    "cp1": "#777777", "cp2": "#FFFC00", "cp3": "#FFFC00",
    "s_fs": 16, "s_fw": 900, "s_wpc": 3, "s_ml": 1,
    "s_sk": 2, "s_as": 1.15, "s_ds": True,
    "s_tt": "uppercase", "s_ff": "'Arial Black', Impact, sans-serif",

    "s_va": "center", "s_vo": 0.2, "s_mw": 70,
    "style_choice_radio": 2,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Normalise string session state — old sessions may have stored title-case values
for _k in ("s_tt", "s_va"):
    if isinstance(st.session_state.get(_k), str):
        st.session_state[_k] = st.session_state[_k].lower()


# ─── HELPERS ──────────────────────────────────────────────────────────────────
def format_title_card(i: int) -> str:
    titles = st.session_state.suggested_titles
    if i < len(titles):
        return titles[i]["title"]
    return "✏️  Other — type my own"


def sync_title():
    idx    = st.session_state.title_radio_widget
    titles = st.session_state.suggested_titles
    if idx < len(titles):
        st.session_state.yt_title_input = titles[idx]["title"]


def build_stroke(size: int, color: str, with_shadow: bool = True) -> str:
    shadow = ""
    if size > 0:
        offsets = [
            f"{dx}px {dy}px 0 {color}"
            for dx in range(-size, size + 1)
            for dy in range(-size, size + 1)
            if not (dx == 0 and dy == 0)
        ]
        shadow = ", ".join(offsets)
    if with_shadow:
        ds = "0px 2px 6px rgba(0,0,0,0.85)"
        shadow = f"{shadow}, {ds}" if shadow else ds
    return shadow or "none"


def extract_subtitle_text(transcription_source) -> str:
    if isinstance(transcription_source, str) and transcription_source.endswith(".srt"):
        try:
            with open(transcription_source, "r", encoding="utf-8") as f:
                raw = f.read()
            raw = re.sub(r"\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n", "", raw)
            return raw.strip()
        except Exception:
            return ""
    elif isinstance(transcription_source, dict):
        words = [w.get("word", "") for seg in transcription_source.get("segments", [])
                 for w in seg.get("words", [])]
        return " ".join(words).strip()
    return ""


# ─── AI TITLE + DESCRIPTION GENERATION ───────────────────────────────────────
def generate_titles_from_subtitles(subtitle_text: str) -> tuple[list[dict], str]:
    try:
        from groq import Groq
    except ImportError:
        return [{"title": "Install groq: pip install groq", "buzz": 85}], ""

    api_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
    if not api_key:
        return [{"title": "Add GROQ_API_KEY to secrets.toml", "buzz": 85}], ""

    client  = Groq(api_key=api_key)
    trimmed = subtitle_text.strip()[:2500]

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            messages=[{
                "role": "system",
                "content": (
                    "You are a YouTube viral growth expert. Given a transcript, produce:\n"
                    "1. Exactly 5 viral YouTube Shorts titles each with a Buzz Meter score (85-100).\n"
                    "   Spread scores so the best title stands out.\n"
                    "2. One high-retention description (max 3 sentences) + 5-7 trending hashtags.\n"
                    "Respond ONLY as valid JSON with two keys: "
                    "'titles' (array of {title, buzz}) and 'description' (string). "
                    "No markdown, no explanation."
                )
            }, {
                "role": "user",
                "content": f"Transcript:\n{trimmed}"
            }],
        )
        import json as _json
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"\n?```$",        "", raw, flags=re.MULTILINE)
        data = _json.loads(raw)

        titles = []
        for item in data.get("titles", [])[:5]:
            buzz = max(85, min(100, int(item.get("buzz", 88))))
            titles.append({"title": str(item.get("title", "Untitled")), "buzz": buzz})

        description = data.get("description", "")
        return titles, description

    except Exception as e:
        return [{"title": f"Error: {e}", "buzz": 85}], ""


# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#0d0d14;border-bottom:1px solid #1a1a24;
    padding:13px 32px;display:flex;align-items:center;justify-content:space-between;">
  <div style="font-family:'Syne',sans-serif;font-size:1.15rem;font-weight:800;
      letter-spacing:-0.01em;color:#e8e8f0">Cap'n'Go</div>
  <div style="color:white;font-size:0.65rem;font-family:'JetBrains Mono',monospace;
      letter-spacing:0.14em;text-transform:uppercase">eMaster Class Academy</div>
</div>
<div style="height:24px"></div>
""", unsafe_allow_html=True)

# ─── LAYOUT ───────────────────────────────────────────────────────────────────
_, col_src, _d1, col_style, _d2, col_preview, _d3, col_publish, _ = st.columns(
    [0.3, 2.8, 0.05, 4.8, 0.05, 5.5, 0.05, 5.5, 0.3], gap="small"
)

# ══════════════════════════════════════════════════════
# COL 01 — SOURCE
# ══════════════════════════════════════════════════════
with col_src:
    st.markdown('<div class="panel-title">01 &nbsp; Source</div>', unsafe_allow_html=True)
    st.markdown('<p class="section-label">Video</p>', unsafe_allow_html=True)

    uploaded_video = st.file_uploader(
        "Upload video", type=["mp4", "mov", "avi", "mkv"],
        key="uploader_video", label_visibility="collapsed")

    if uploaded_video:
        nm = uploaded_video.name
        st.markdown(
            f'<span class="pill pill-green" style="margin-top:6px;display:inline-block">'
            f'✓ {nm[:18]+"…" if len(nm) > 18 else nm} · {uploaded_video.size/1048576:.1f} MB</span>',
            unsafe_allow_html=True)

    st.markdown(
        '<p class="section-label">Script '
        '<span style="font-size:0.68rem;font-weight:400">(Optional)</span></p>',
        unsafe_allow_html=True)

    script_mode_pick = st.selectbox(
        "Script mode", options=["default", "upload", "type"],
        format_func=lambda x: {
            "default": "Auto-detect",
            "upload":  "Upload .srt",
            "type":    "Type / paste ",
        }[x],
        index=["default", "upload", "type"].index(st.session_state.script_mode),
        key="script_mode_select", label_visibility="collapsed")

    if script_mode_pick != st.session_state.script_mode:
        st.session_state.script_mode = script_mode_pick
        st.rerun()

    uploaded_srt = None
    caption_text = ""

    if st.session_state.script_mode == "upload":
        uploaded_srt = st.file_uploader(
            "Upload SRT", type=["srt"],
            key="uploader_srt", label_visibility="collapsed")
        if uploaded_srt:
            st.markdown('<span class="pill pill-blue" style="margin-top:6px;display:inline-block">📄 SRT loaded</span>',
                        unsafe_allow_html=True)
    elif st.session_state.script_mode == "type":
        caption_text = st.text_area(
            "Script", value=st.session_state.caption_text, height=100,
            placeholder="Type or paste what's spoken…",
            key="caption_input", label_visibility="collapsed")
        st.session_state.caption_text = caption_text

# ══════════════════════════════════════════════════════
# COL 02 — STYLE
# ══════════════════════════════════════════════════════
with col_style:
    st.markdown('<div class="panel-title">02 &nbsp; Style</div>', unsafe_allow_html=True)
    st.markdown('<p class="section-label">Caption Template</p>', unsafe_allow_html=True)

    _bc1, _bc2 = st.columns(2, gap="small")
    for i, key in enumerate(TEMPLATES.keys()):
        with (_bc1 if i % 2 == 0 else _bc2):
            if st.button(key, key=f"tpl_{key}", use_container_width=True,
                         type="primary" if key == st.session_state.selected_template else "secondary"):
                st.session_state.selected_template = key
                st.rerun()

    # Sync widget session state defaults when template changes
    if st.session_state.selected_template != st.session_state.get("_prev_template"):
        tpl = TEMPLATES[st.session_state.selected_template]
        st.session_state.update({
            "cp1": tpl["inactive_color"], "cp2": tpl["active_color"], "cp3": tpl["highlight_color"],
            "s_fs": tpl["font_size"], "s_fw": tpl["font_weight"], "s_wpc": tpl["max_words_per_chunk"],
            "s_ml": tpl["max_lines"], "s_sk": tpl["stroke_size"], "s_as": tpl["active_scale"],
            "s_ds": tpl["drop_shadow"], "s_tt": tpl["text_transform"], "s_ff": tpl["font_family"],
            "s_va": tpl["vertical_align"], "s_vo": tpl["vertical_offset"],
            "s_mw": int(tpl["max_width_pct"] * 100),
            "style_choice_radio": tpl["style_choice"],
        })
        st.session_state["_prev_template"] = st.session_state.selected_template

    tpl = TEMPLATES[st.session_state.selected_template]

    with st.expander("⚙️  Advanced settings", expanded=False):
        st.markdown('<p class="adv-heading">Colours</p>', unsafe_allow_html=True)
        cc1, cc2, cc3 = st.columns(3)
        with cc1: st.color_picker("Inactive",  st.session_state["cp1"], key="cp1")
        with cc2: st.color_picker("Active",    st.session_state["cp2"], key="cp2")
        with cc3: st.color_picker("Highlight", st.session_state["cp3"], key="cp3")

        st.markdown('<p class="adv-heading">Animation style</p>', unsafe_allow_html=True)
        st.radio(
            "Animation", options=[1, 2, 3],
            format_func=lambda x: {1: "Highlight box", 2: "Colour pop", 3: "Glow"}[x],
            index=[1, 2, 3].index(st.session_state["style_choice_radio"]),
            horizontal=True, label_visibility="collapsed",
            key="style_choice_radio")

        st.markdown('<p class="adv-heading">Typography</p>', unsafe_allow_html=True)
        adv1, adv2, adv3 = st.columns(3)
        with adv1:
            st.slider("Font size (px)", 10, 48, st.session_state["s_fs"], key="s_fs")
            st.slider("Words per chunk", 1, 6, st.session_state["s_wpc"], key="s_wpc")
            st.selectbox("Text case", ["uppercase", "none", "capitalize"],
                         index=["uppercase", "none", "capitalize"].index(st.session_state["s_tt"]),
                         key="s_tt")
        with adv2:
            st.selectbox("Font weight", [400, 700, 900],
                         index=[400, 700, 900].index(st.session_state["s_fw"]),
                         key="s_fw")
            st.slider("Max lines", 1, 4, st.session_state["s_ml"], key="s_ml")
            st.text_input("Font family CSS", value=st.session_state["s_ff"], key="s_ff")
        with adv3:
            st.slider("Active word scale", 1.0, 2.0, st.session_state["s_as"], step=0.05, key="s_as")
            st.slider("Stroke width (px)", 0, 8, st.session_state["s_sk"], key="s_sk")
            st.checkbox("Drop shadow", value=st.session_state["s_ds"], key="s_ds")

        st.markdown('<p class="adv-heading">Position</p>', unsafe_allow_html=True)
        pos1, pos2, pos3 = st.columns(3)
        with pos1:
            st.selectbox("Vertical", ["bottom", "center", "top"],
                         index=["bottom", "center", "top"].index(st.session_state["s_va"]),
                         key="s_va")
        with pos2:
            st.slider("Offset", -1.0, 1.0, st.session_state["s_vo"], step=0.05, key="s_vo")
        with pos3:
            st.slider("Max width %", 40, 100, st.session_state["s_mw"], key="s_mw")

    # ── FIX: Always read final values from session state ──────────────────────
    inactive_color      = st.session_state["cp1"]
    active_color        = st.session_state["cp2"]
    highlight_color     = st.session_state["cp3"]
    style_choice        = st.session_state["style_choice_radio"]
    font_size           = st.session_state["s_fs"]
    font_weight         = st.session_state["s_fw"]
    max_words_per_chunk = st.session_state["s_wpc"]
    max_lines           = st.session_state["s_ml"]
    stroke_size         = st.session_state["s_sk"]
    active_scale        = st.session_state["s_as"]
    drop_shadow         = st.session_state["s_ds"]
    text_transform      = st.session_state["s_tt"]
    font_family         = st.session_state["s_ff"]
    vertical_align      = st.session_state["s_va"]
    vertical_offset     = st.session_state["s_vo"]
    max_width_pct       = st.session_state["s_mw"] / 100
    # ─────────────────────────────────────────────────────────────────────────

    # Reset state when a new video is uploaded
    if st.session_state.uploaded_video_prev != uploaded_video:
        st.session_state.generate_clicked    = False
        st.session_state.titles_generated    = False
        st.session_state.suggested_titles    = []
        st.session_state.generated_description = ""
        st.session_state.output_video_bytes  = None
    st.session_state.uploaded_video_prev = uploaded_video

    generate = st.button(
        "Generate Captions",
        type="primary" if st.session_state.generate_clicked else "secondary",
        use_container_width=True,
        disabled=not uploaded_video)

    if generate:
        st.session_state.generate_clicked      = True
        st.session_state.is_generating         = True
        st.session_state.titles_generated      = False
        st.session_state.suggested_titles      = []
        st.session_state.generated_description = ""
        st.session_state.output_video_bytes    = None

# ══════════════════════════════════════════════════════
# COL 03 — PREVIEW
# ══════════════════════════════════════════════════════
with col_preview:
    st.markdown('<div class="panel-title">03 &nbsp; Preview</div>', unsafe_allow_html=True)

    if st.session_state.is_generating:
        st.markdown("""
        <div class="loading-box">
            <div class="spinner"></div>
            <div class="loading-label">Generating captions…</div>
        </div>""", unsafe_allow_html=True)
    elif st.session_state.output_video_bytes:
        _, preview_col, _ = st.columns([1, 3, 1])
        with preview_col:
            st.video(st.session_state.output_video_bytes)
        st.download_button(
            "Download HD",
            data=st.session_state.output_video_bytes,
            file_name="capngo.mp4", mime="video/mp4",
            use_container_width=True, type="primary")
    else:
        st.markdown("""
        <div class="output-placeholder">
            <div style="font-size:2rem">🎬</div>
            <div>Preview appears here</div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# COL 04 — PUBLISH
# ══════════════════════════════════════════════════════
with col_publish:
    st.markdown('<div class="panel-title">04 &nbsp; Publish</div>', unsafe_allow_html=True)

    titles_data = st.session_state.get("suggested_titles", [])
    description = st.session_state.get("generated_description", "")

    # ── Titles ────────────────────────────────────────────────────────────────
    if titles_data:
        for i, item in enumerate(titles_data):
            score_val = item['buzz']
            score_color = "#97eb64" if score_val >= 90 else "#e1ad3a"
            title_text = item['title']

            col1, col2, col3 = st.columns([1, 8, 1])

            with col1:
                st.markdown(
                    f"<div style='display:flex; align-items:center; height:40px;'>"
                    f"<span style='color:{score_color}; font-weight:bold'>{score_val}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

            with col2:
                st.markdown(
                    f"<div style='display:flex; align-items:center; height:40px;'>"
                    f"{title_text}"
                    f"</div>",
                    unsafe_allow_html=True
                )

            with col3:
                safe_title = title_text.replace("`", "\\`").replace("\\", "\\\\")

                components.html(f"""
                    <style>
                        * {{ margin:0; padding:0; box-sizing:border-box; }}
                        body {{ background:transparent; }}
                        .cb {{
                            background:transparent; border:none;
                            color:#5a5a72; cursor:pointer; font-size:1rem;
                            height:40px; width:100%; display:flex;
                            align-items:center; justify-content:center;
                            transition: color 0.15s;
                        }}
                        .cb:hover {{ color:#e8e8f0; }}
                        .cb.ok {{ color:#00ff41; }}
                    </style>
                    <button class="cb" id="b{i}" onclick="
                        navigator.clipboard.writeText(`{safe_title}`);
                        this.innerText='✓';
                        this.classList.add('ok');
                        setTimeout(()=>{{
                            this.innerText='📋';
                            this.classList.remove('ok');
                        }},1500);
                    ">📋</button>
                """, height=40)

    else:
        st.caption("✨ Title suggestions appear here after generation.")

    # ── Description ───────────────────────────────────────────────────────────
    if description:
        desc_safe = description.replace("`", "\\`").replace("\\", "\\\\")
        components.html(f"""
            <style>
                * {{ box-sizing:border-box; margin:0; padding:0; }}
                body {{ background:transparent; }}
                .hdr {{
                    display:flex; align-items:center;
                    justify-content:space-between; margin-bottom:6px;
                }}
                .lbl {{
                    font-size:0.78rem; font-weight:700;
                    color:#e8e8f0; font-family:'Syne',sans-serif;
                }}
                .btn {{
                    background:transparent; border:1px solid #2e2e3d;
                    border-radius:6px; color:#5a5a72; cursor:pointer;
                    font-size:0.65rem; font-family:'JetBrains Mono',monospace;
                    padding:3px 8px; transition:all 0.15s;
                    display:flex; align-items:center; gap:4px;
                }}
                .btn:hover {{ color:#e8e8f0; border-color:#5a5a72; }}
                .btn.ok   {{ color:#00ff41; border-color:#00ff41; }}
                .box {{
                    background:#16161e; border:1px solid #2e2e3d;
                    border-radius:10px; padding:10px 12px;
                    color:#e8e8f0; font-size:0.78rem;
                    font-family:'Syne',sans-serif; line-height:1.55;
                    white-space:pre-wrap; word-break:break-word;
                }}
            </style>
            <div class="hdr">
                <span class="lbl">Description</span>
                <button class="btn" id="cb" onclick="copy()">📋 Copy</button>
            </div>
            <div class="box" id="txt">{description}</div>
            <script>
                function copy() {{
                    navigator.clipboard.writeText(
                        document.getElementById('txt').innerText
                    ).then(() => {{
                        const b = document.getElementById('cb');
                        b.innerHTML = '✓ Copied';
                        b.classList.add('ok');
                        setTimeout(() => {{
                            b.innerHTML = '📋 Copy';
                            b.classList.remove('ok');
                        }}, 1500);
                    }});
                }}
            </script>
        """, height=150)

# ══════════════════════════════════════════════════════
# PROCESSING — runs only when Generate is clicked
# ══════════════════════════════════════════════════════
if uploaded_srt:
    script_mode  = "srt"
    srt_text_raw = uploaded_srt.read().decode("utf-8")
elif caption_text.strip():
    script_mode = "text"
else:
    script_mode = "auto"

if generate and uploaded_video:
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path  = os.path.join(tmpdir, "input_video.mp4")
        output_path = os.path.join(tmpdir, "output_video.mp4")

        with open(input_path, "wb") as f:
            f.write(uploaded_video.read())

        # Duration guard
        try:
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", input_path],
                capture_output=True, text=True, timeout=30)
            if float(probe.stdout.strip()) > MAX_DURATION_SECONDS:
                st.session_state.is_generating = False
                st.error(f"Video exceeds {MAX_DURATION_SECONDS}s limit.")
                st.stop()
        except Exception:
            pass

        # Transcription
        if script_mode == "srt":
            srt_path = os.path.join(tmpdir, "input.srt")
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt_text_raw)
            transcription_source = srt_path
        else:
            try:
                import stable_whisper
            except ImportError:
                st.error("Run: pip install stable-ts")
                st.stop()
            model = stable_whisper.load_model("base")
            try:
                if script_mode == "text":
                    transcription_source = model.align(
                        input_path, caption_text.strip(), language="en").to_dict()
                else:
                    transcription_source = model.transcribe(
                        input_path, language="en", word_timestamps=True, temperature=0.0).to_dict()
            except Exception as e:
                st.error(f"Transcription failed: {e}")
                st.stop()

        # Caption rendering
        SC       = "#000000"
        base_shd = build_stroke(stroke_size, SC, drop_shadow)
        glow_shd = (f"{build_stroke(stroke_size, SC, False)}, "
                    f"0 0 10px {highlight_color}, 0 0 28px {highlight_color}, "
                    f"0 0 50px {highlight_color}88")
        CHARS = max(24, max_words_per_chunk * 10)

        word_css = f"""
        .caps-container {{
            display:flex; flex-wrap:wrap; justify-content:center;
            align-items:center; column-gap:0; row-gap:0;
            line-height:1.3; letter-spacing:0.01em;
        }}
        .word {{
            color:{inactive_color}; font-weight:{font_weight};
            font-size:{font_size}px; text-transform:{text_transform};
            font-family:{font_family}; display:inline-block;
            padding:2px 1px; text-shadow:{base_shd};
        }}
        .word-already-narrated {{ color:{inactive_color} !important; text-shadow:{base_shd}; }}
        """
        if style_choice == 1:
            word_css += (f".word-being-narrated {{ color:{active_color} !important; "
                         f"background:{highlight_color}; padding:2px 1px; border-radius:1px; "
                         f"text-shadow:none; font-size:{int(font_size*active_scale)}px; }}")
        elif style_choice == 2:
            word_css += (f".word-being-narrated {{ color:{highlight_color} !important; "
                         f"text-shadow:{base_shd}; font-size:{int(font_size*active_scale)}px; }}")
        else:
            word_css += (f".word-being-narrated {{ color:{active_color} !important; "
                         f"text-shadow:{glow_shd}; font-size:{int(font_size*active_scale)}px; }}")

        va_map = {
            "bottom": VerticalAlignmentType.BOTTOM,
            "center": VerticalAlignmentType.CENTER,
            "top":    VerticalAlignmentType.TOP,
        }
        layout_options = SubtitleLayoutOptions(
            vertical_align=VerticalAlignment(
                align=va_map[vertical_align], offset=vertical_offset),
            max_width_ratio=max_width_pct,
            max_number_of_lines=max_lines)

        try:
            (CapsPipelineBuilder()
             .with_input_video(input_path)
             .with_output_video(output_path)
             .with_transcription(transcription_source)
             .add_css_content(word_css)
             .add_segment_splitter(LimitByCharsSplitter(CHARS))
             .with_layout_options(layout_options)
             .build()
             .run())
        except Exception as e:
            st.session_state.is_generating = False
            st.error(f"Rendering failed: {e}")
            st.stop()

        with open(output_path, "rb") as f:
            st.session_state.output_video_bytes = f.read()

        # AI title + description generation
        subtitle_plain = extract_subtitle_text(transcription_source)
        if subtitle_plain:
            with st.spinner("✨ Scoring titles with Buzz Meter…"):
                titles, desc = generate_titles_from_subtitles(subtitle_plain)
            st.session_state.suggested_titles      = titles
            st.session_state.generated_description = desc
            st.session_state.selected_title_idx    = 0
            st.session_state.titles_generated      = True

        st.session_state.is_generating = False
        st.rerun()