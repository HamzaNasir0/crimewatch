import requests
import folium
import math
from collections import Counter
import streamlit as st
from streamlit_folium import st_folium

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="UK Crime Map", page_icon="🔍", layout="wide")

# ── Session state defaults ────────────────────────────────────────────────────
for key, default in {
    "dark_mode": True,
    "crimes":    None,
    "lat":       None,
    "lng":       None,
    "searched_postcode": "",
    "hidden_cats": set(),
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode

dark = st.session_state.dark_mode

# ── Theme tokens ──────────────────────────────────────────────────────────────
if dark:
    bg         = "#0e0e12"
    sidebar_bg = "#16161e"
    card_bg    = "#1a1a24"
    border     = "#2a2a3a"
    row_border = "#1e1e2a"
    badge_bg   = "#1e1e2a"
    bar_track  = "#1e1e2a"
    text       = "#e8e8e8"
    muted      = "#888"
    footer_col = "#555"
    map_tiles  = "cartodbdark_matter"
    toggle_icon  = "☀️"
    toggle_label = "Light Mode"
else:
    bg         = "#f5f5f0"
    sidebar_bg = "#e8e8e2"
    card_bg    = "#ffffff"
    border     = "#d8d8d0"
    row_border = "#e5e5e0"
    badge_bg   = "#ececec"
    bar_track  = "#e0e0da"
    text       = "#1a1a1a"
    muted      = "#666"
    footer_col = "#999"
    map_tiles  = "cartodbpositron"
    toggle_icon  = "🌙"
    toggle_label = "Dark Mode"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap');

  html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif; }}
  h1, h2, h3 {{ font-family: 'Space Mono', monospace !important; }}

  .stApp, .stApp > div, [data-testid="stAppViewContainer"] {{
      background-color: {bg} !important;
      color: {text} !important;
  }}

  /* Sidebar — target every layer Streamlit wraps it in */
  [data-testid="stSidebar"],
  [data-testid="stSidebar"] > div,
  [data-testid="stSidebar"] > div > div,
  [data-testid="stSidebarContent"] {{
      background-color: {sidebar_bg} !important;
  }}
  [data-testid="stSidebar"] * {{ color: {text} !important; }}
  [data-testid="stSidebar"] hr {{ border-color: {border} !important; }}

  /* Inputs */
  .stTextInput > div > div > input {{
      background: {card_bg} !important;
      color: {text} !important;
      border: 1px solid {border} !important;
      border-radius: 6px !important;
  }}
  .stSelectbox > div > div {{
      background: {card_bg} !important;
      color: {text} !important;
      border: 1px solid {border} !important;
      border-radius: 6px !important;
  }}
  [data-baseweb="select"] div, [data-baseweb="popover"] li {{
      background: {card_bg} !important;
      color: {text} !important;
  }}

  /* Buttons */
  .stButton > button {{
      background: #e05c5c !important;
      color: white !important;
      border: none !important;
      border-radius: 6px !important;
      font-family: 'Space Mono', monospace !important;
      font-weight: 700 !important;
      letter-spacing: 0.05em !important;
      width: 100% !important;
      transition: background 0.2s !important;
  }}
  .stButton > button:hover {{ background: #c94444 !important; }}

  /* Metric cards */
  .metric-card {{
      background: {card_bg};
      border: 1px solid {border};
      border-radius: 8px;
      padding: 16px 20px;
      text-align: center;
  }}
  .metric-value {{
      font-family: 'Space Mono', monospace;
      font-size: 2rem;
      font-weight: 700;
      color: #e05c5c;
  }}
  .metric-label {{
      font-size: 0.78rem;
      color: {muted};
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-top: 4px;
  }}

  /* Crime rows */
  .crime-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 7px 0;
      border-bottom: 1px solid {row_border};
      font-size: 0.88rem;
      color: {text};
  }}
  .crime-dot {{
      width: 10px; height: 10px;
      border-radius: 50%;
      display: inline-block;
      margin-right: 8px;
  }}
  .crime-badge {{
      background: {badge_bg};
      border-radius: 12px;
      padding: 2px 10px;
      font-family: 'Space Mono', monospace;
      font-size: 0.8rem;
      color: {text};
  }}
  .bar-track {{
      background: {bar_track};
      border-radius: 3px;
      height: 3px;
      margin-bottom: 4px;
  }}

  div[data-testid="stAlert"] {{ border-radius: 6px; }}
  p, label {{ color: {text} !important; }}
</style>
""", unsafe_allow_html=True)

# ── Crime styles ──────────────────────────────────────────────────────────────
CRIME_STYLES = {
    'robbery':                      ('#000000', 'Robbery'),
    'possession-of-weapons':        ('#8B0000', 'Weapons'),
    'violence-and-sexual-offences': ('#FF0000', 'Violent Crime'),
    'criminal-damage-arson':        ('#FF4500', 'Arson / Damage'),
    'burglary':                     ('#FF8C00', 'Burglary'),
    'vehicle-crime':                ('#FFA500', 'Vehicle Crime'),
    'drugs':                        ('#FFD700', 'Drugs'),
    'theft-from-the-person':        ('#EEEE00', 'Theft From Person'),
    'shoplifting':                  ('#FFFF00', 'Shoplifting'),
    'other-theft':                  ('#DA70D6', 'Other Theft'),
    'bicycle-theft':                ('#D8BFD8', 'Bicycle Theft'),
    'public-order':                 ('#ADFF2F', 'Public Order'),
    'anti-social-behaviour':        ('#90EE90', 'Anti-Social Behaviour'),
    'other-crime':                  ('#00FF00', 'Other Crime'),
}
SEVERITY_ORDER = list(CRIME_STYLES.keys())

def get_crime_style(category):
    return CRIME_STYLES.get(category, ('#808080', 'Unknown'))

# ── API helpers ───────────────────────────────────────────────────────────────
def get_coords(postcode):
    try:
        res = requests.get(
            f"https://api.postcodes.io/postcodes/{postcode.replace(' ', '')}",
            timeout=8,
        ).json()
        if res['status'] == 200:
            return res['result']['latitude'], res['result']['longitude']
    except Exception:
        pass
    return None, None

def get_bounding_poly(lat, lng, miles):
    lat_d = miles / 69.0
    lng_d = miles / (69.0 * math.cos(math.radians(lat)))
    return ":".join([
        f"{lat + lat_d},{lng}", f"{lat},{lng + lng_d}",
        f"{lat - lat_d},{lng}", f"{lat},{lng - lng_d}",
    ])

def fetch_crimes(lat, lng, radius_miles):
    resp = requests.get(
        "https://data.police.uk/api/crimes-street/all-crime",
        params={'poly': get_bounding_poly(lat, lng, radius_miles)},
        timeout=30,
    )
    return resp.json() if resp.status_code == 200 else None

def build_map(lat, lng, crimes, tiles, hidden_cats=None):
    if hidden_cats is None:
        hidden_cats = set()
    m = folium.Map(location=[lat, lng], zoom_start=14, tiles=tiles)
    layers = {}
    for crime in crimes:
        if crime['category'] in hidden_cats:
            continue
        c_lat = float(crime['location']['latitude'])
        c_lng = float(crime['location']['longitude'])
        color, label = get_crime_style(crime['category'])
        if label not in layers:
            layers[label] = folium.FeatureGroup(name=label)
        popup_html = (
            f"<div style='font-family:Arial;width:180px;'>"
            f"<b style='color:{color};'>{label}</b><br>"
            f"<small>{crime.get('month','')}</small><br>"
            f"<hr style='margin:5px 0;'>{crime['location']['street']['name']}</div>"
        )
        folium.CircleMarker(
            location=[c_lat, c_lng], radius=6,
            popup=folium.Popup(popup_html, max_width=250),
            color=color, fill=True, fill_opacity=0.75, weight=1,
        ).add_to(layers[label])

    added = set()
    for cat in SEVERITY_ORDER:
        _, lbl = get_crime_style(cat)
        if lbl in layers and lbl not in added:
            layers[lbl].add_to(m); added.add(lbl)
    for lbl, lg in layers.items():
        if lbl not in added:
            lg.add_to(m)

    # LayerControl removed — sidebar handles filtering
    folium.Marker(
        [lat, lng],
        icon=folium.Icon(color='blue', icon='home', prefix='fa'),
        tooltip="Search location",
    ).add_to(m)
    return m

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Search")
    postcode = st.text_input("Postcode", placeholder="e.g. SW1A 1AA")
    radius   = st.selectbox("Radius (miles)", [1, 2, 3], index=0)
    search   = st.button("Generate Map")
    st.button(f"{toggle_icon} {toggle_label}", on_click=toggle_theme)

    st.markdown("---")
    st.markdown("### Filters")

    # Show All / Hide All — write directly into checkbox keys so they re-render correctly
    def show_all():
        st.session_state.hidden_cats = set()
        for cat in SEVERITY_ORDER:
            st.session_state[f"chk_{cat}"] = True

    def hide_all():
        st.session_state.hidden_cats = set(SEVERITY_ORDER)
        for cat in SEVERITY_ORDER:
            st.session_state[f"chk_{cat}"] = False

    col_a, col_b = st.columns(2)
    with col_a:
        st.button("Show All", key="show_all", on_click=show_all)
    with col_b:
        st.button("Hide All", key="hide_all", on_click=hide_all)

    for cat in SEVERITY_ORDER:
        color, label = get_crime_style(cat)
        # Initialise checkbox key from hidden_cats on first run
        if f"chk_{cat}" not in st.session_state:
            st.session_state[f"chk_{cat}"] = cat not in st.session_state.hidden_cats
        new_checked = st.checkbox(
            label, key=f"chk_{cat}",
            label_visibility="collapsed",
        )
        # Render coloured dot + label overlaid on the checkbox
        st.markdown(
            f"<div style='margin-top:-2.6rem;margin-left:1.8rem;"
            f"font-size:0.88rem;color:{text};pointer-events:none;'>"
            f"<span style='display:inline-block;width:10px;height:10px;"
            f"border-radius:50%;background:{color};margin-right:8px;'></span>"
            f"{label}</div>",
            unsafe_allow_html=True,
        )
        if new_checked:
            st.session_state.hidden_cats.discard(cat)
        else:
            st.session_state.hidden_cats.add(cat)

    st.markdown(
        f"<p style='color:{footer_col};font-size:0.75rem;margin-top:12px;'>"
        f"Data: data.police.uk · Most recent month available</p>",
        unsafe_allow_html=True,
    )

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🔍 UK Crime Map")
st.markdown(
    f"<p style='color:{muted};margin-top:-12px;font-size:0.9rem;'>"
    f"Visualise street-level crime data from the UK Police API</p>",
    unsafe_allow_html=True,
)

# ── Handle new search (stores results in session_state) ───────────────────────
if search:
    if not postcode.strip():
        st.error("Please enter a postcode.")
    else:
        with st.spinner("Geocoding postcode…"):
            lat, lng = get_coords(postcode.strip())
        if lat is None:
            st.error("Postcode not found. Please check and try again.")
        else:
            with st.spinner(f"Fetching crime data for {radius} mile(s) around **{postcode.upper()}**…"):
                crimes = fetch_crimes(lat, lng, radius)
            if crimes is None:
                st.error("The Police API returned an error — try a smaller radius.")
            elif len(crimes) == 0:
                st.warning("No crime records found for this area.")
            else:
                st.session_state.crimes = crimes
                st.session_state.lat    = lat
                st.session_state.lng    = lng
                st.session_state.searched_postcode = postcode.upper()

# ── Render (reads from session_state — survives theme toggle reruns) ──────────
if st.session_state.crimes:
    crimes = st.session_state.crimes
    lat    = st.session_state.lat
    lng    = st.session_state.lng

    counts  = Counter(c['category'] for c in crimes)
    top_cat = counts.most_common(1)[0]
    _, top_label = get_crime_style(top_cat[0])

    c1, c2, c3 = st.columns(3)
    for col, value, label, fsize in [
        (c1, f"{len(crimes):,}", "Total incidents",              "2rem"),
        (c2, str(len(counts)),   "Crime categories",             "2rem"),
        (c3, top_label,          f"Most common ({top_cat[1]:,})", "1.15rem"),
    ]:
        with col:
            st.markdown(
                f"<div class='metric-card'>"
                f"<div class='metric-value' style='font-size:{fsize};'>{value}</div>"
                f"<div class='metric-label'>{label}</div></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    map_col, stat_col = st.columns([3, 1])

    with map_col:
        folium_map = build_map(lat, lng, crimes, tiles=map_tiles, hidden_cats=st.session_state.hidden_cats)
        st_folium(folium_map, width=None, height=560, returned_objects=[])

    with stat_col:
        st.markdown(
            f"<p style='font-family:Space Mono,monospace;font-size:0.8rem;"
            f"color:{muted};text-transform:uppercase;letter-spacing:0.08em;"
            f"margin-bottom:10px;'>Breakdown</p>",
            unsafe_allow_html=True,
        )
        for cat in SEVERITY_ORDER:
            if cat not in counts:
                continue
            color, label = get_crime_style(cat)
            n   = counts[cat]
            pct = n / len(crimes) * 100
            st.markdown(
                f"<div class='crime-row'>"
                f"<span><span class='crime-dot' style='background:{color};'></span>{label}</span>"
                f"<span class='crime-badge'>{n}</span></div>"
                f"<div class='bar-track'>"
                f"<div style='background:{color};width:{pct:.1f}%;height:3px;border-radius:3px;'></div>"
                f"</div>",
                unsafe_allow_html=True,
            )
else:
    st.markdown(
        f"<div style='text-align:center;padding:80px 0;'>"
        f"<p style='font-size:3rem;'>🗺️</p>"
        f"<p style='font-family:Space Mono,monospace;color:{muted};'>"
        f"Enter a postcode in the sidebar to begin</p></div>",
        unsafe_allow_html=True,
    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    f"<div style='position:fixed;bottom:0;left:0;right:0;padding:12px 24px;"
    f"background:{sidebar_bg};border-top:1px solid {border};text-align:center;"
    f"font-family:Space Mono,monospace;font-size:0.78rem;z-index:9999;'>"
    f"made by <a href='https://github.com/HamzaNasir0' target='_blank' "
    f"style='color:#e05c5c;text-decoration:none;font-weight:700;'>hammy</a> 🔴"
    f"</div>",
    unsafe_allow_html=True,
)
