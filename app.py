"""ARAKONAK GES — Kontrol Panosu (v4 · Açık Kurumsal / Power BI tarzı).

Sol menü rayı · KPI kartları · kombine grafik · halka gösterge · koşullu
biçimlendirmeli disiplin matrisi. İş kalemleri günlük girilir; her gün otomatik
'günlük anlık görüntü' kaydedilir ve S-eğrisi bu günlük noktalardan oluşur.
"""
from __future__ import annotations

import base64
import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

import auth
import core
import charts
import exports
import storage

st.set_page_config(page_title="ARAKONAK GES — Kontrol Panosu", page_icon="⚡",
                   layout="wide", initial_sidebar_state="expanded")

_HERE = Path(__file__).parent


def _asset(*names):
    for n in names:
        for c in (_HERE / "assets" / "fonts" / n, _HERE / "assets" / n, _HERE / n):
            if c.exists():
                return c
    return _HERE / names[0]


@st.cache_data(show_spinner=False)
def _logo(color):
    try:
        svg = _asset("logo.svg").read_text(encoding="utf-8")
        if color == "black":
            svg = svg.replace("fill:#fff", "fill:#0a0a0a").replace('fill="#fff"', 'fill="#0a0a0a"')
        return base64.b64encode(svg.encode()).decode()
    except Exception:
        return None


LOGO_WHITE = _logo("white")
LOGO_BLACK = _logo("black")

TEAL = "#2dd4bf"; TEAL_D = "#14b8a6"; INDIGO = "#0e7490"
GREEN = "#34d399"; AMBER = "#fbbf24"; RED = "#fb7185"; SLATE = "#e6f4f4"; MUTED = "#7fb0b3"


# ────────────────────── STİL (Açık Kurumsal) ──────────────────────
# ────────────────────── TEMA PALETLERİ ──────────────────────
THEMES = {
    "dark": dict(
        bg="radial-gradient(760px 520px at 50% -18%, rgba(34,211,238,.16), transparent 60%),"
           "radial-gradient(700px 500px at 100% 8%, rgba(139,92,246,.10), transparent 55%),"
           "linear-gradient(160deg,#04060d,#05080f 60%,#04060d)",
        text="#dbeafe", muted="#5f7a99", panel="#0a1422", border="#12324a",
        rail="#070d18", railb="#12324a", railtxt="#5f9bbf", railhov="#0d1a2c",
        acc="#22d3ee", acc2="#0891b2", accd="#0891b2", ttl="#67e8f9",
        rowb="#0e2233", rowh="#0c1a2a", metricbg="#0a1422"),
    "light": dict(
        bg="radial-gradient(1000px 560px at 8% -8%, rgba(13,148,136,.10), transparent 60%),"
           "radial-gradient(900px 560px at 100% -4%, rgba(99,102,241,.08), transparent 55%),"
           "linear-gradient(160deg,#eef2f7 0%,#f5f8fc 60%,#eef2f7 100%)",
        text="#0f2b3a", muted="#6b8a90", panel="#ffffff", border="#e7edf3",
        rail="#ffffff", railb="#e5ecf2", railtxt="#5b7a82", railhov="#f1f6f6",
        acc="#0d9488", acc2="#6366f1", accd="#0a7268", ttl="#0f3b44",
        rowb="#eef2f6", rowh="#f7fafb", metricbg="#ffffff"),
}


def inject_css(theme="dark"):
    t = THEMES.get(theme, THEMES["dark"])
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    .stApp{{font-family:'Inter','Segoe UI',sans-serif;}}
    [data-testid="stTextInputRevealButton"]{{display:none !important;}}
    #MainMenu, footer{{visibility:hidden;}}
    header[data-testid="stHeader"]{{display:none;}}
    [data-testid="stToolbar"]{{display:none;}}
    .stApp{{background:{t['bg']};}}
    .block-container{{padding-top:1.1rem;padding-bottom:2rem;max-width:1560px;}}
    .stApp, .stApp p, .stApp label, .stApp span, .stApp li{{color:{t['text']};}}

    /* ── SOL RAY ── */
    section[data-testid="stSidebar"]{{background:{t['rail']};border-right:1px solid {t['railb']};width:238px !important;}}
    /* Sidebar HER ZAMAN AÇIK — kapatma butonu gizli (mahsur kalma önlenir) */
    [data-testid="stSidebarCollapseButton"]{{display:none !important;}}
    [data-testid="stExpandSidebarButton"]{{display:none !important;}}
    section[data-testid="stSidebar"]{{
        transform:none !important;visibility:visible !important;
        min-width:238px !important;margin-left:0 !important;}}
    section[data-testid="stSidebar"][aria-expanded="false"]{{
        transform:none !important;margin-left:0 !important;}}
    .rail-logo{{text-align:center;padding:6px 8px 14px;border-bottom:1px solid {t['railb']};margin-bottom:10px;}}
    .rail-logo img{{height:46px;}}
    section[data-testid="stSidebar"] [role="radiogroup"]{{gap:3px;}}
    section[data-testid="stSidebar"] [role="radiogroup"] label{{
      padding:10px 13px;border-radius:11px;margin:1px 6px;cursor:pointer;font-weight:700;font-size:13.5px;
      color:{t['railtxt']};transition:background .12s;}}
    section[data-testid="stSidebar"] [role="radiogroup"] label:hover{{background:{t['railhov']};}}
    section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){{
      background:linear-gradient(120deg,{t['accd']},{t['acc']});color:#04222b;box-shadow:0 8px 18px rgba(34,211,238,.25);}}
    section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) *{{color:#04222b !important;}}
    section[data-testid="stSidebar"] .stButton button{{
      background:{t['railhov']};border:1px solid {t['railb']};color:{t['text']};font-weight:700;border-radius:10px;}}
    .rail-user{{background:{t['railhov']};border:1px solid {t['railb']};border-radius:12px;padding:10px 12px;
      font-size:11.5px;color:{t['muted']};margin:6px 0;}}
    .rail-sec{{font-size:10px;font-weight:800;color:{t['muted']};letter-spacing:.6px;margin:10px 12px 2px;}}

    /* ── ÜST BAŞLIK ── */
    .pagehd h1{{font-size:23px;font-weight:900;color:{t['text']};margin:0;background:none;}}
    .pagehd .sub{{font-size:12px;color:{t['muted']};font-weight:600;margin-top:3px;}}

    /* Kapsam butonları — okunur, tamamen kontrol bizde (primaryColor'dan bağımsız) */
    div[data-testid="stButton"] button[kind="secondary"],
    div[data-testid="stFormSubmitButton"] button[kind="secondary"],
    div[data-testid="stDownloadButton"] button{{
      font-weight:800 !important;border-radius:10px !important;
      background:{t['railhov']} !important;border:1px solid {t['border']} !important;
      color:{t['text']} !important;box-shadow:none !important;}}
    div[data-testid="stButton"] button[kind="secondary"]:hover,
    div[data-testid="stDownloadButton"] button:hover{{
      border-color:{t['acc']} !important;color:{t['acc']} !important;}}
    div[data-testid="stButton"] button[kind="primary"],
    div[data-testid="stFormSubmitButton"] button[kind="primary"]{{
      font-weight:800 !important;border-radius:10px !important;
      background:linear-gradient(120deg,{t['accd']},{t['acc']}) !important;
      color:#04222b !important;border:none !important;
      box-shadow:0 6px 16px rgba(34,211,238,.35) !important;}}
    div[data-testid="stButton"] button[kind="primary"] *,
    div[data-testid="stFormSubmitButton"] button[kind="primary"] *{{color:#04222b !important;}}
    div[data-testid="stButton"] button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover{{filter:brightness(1.08);}}

    /* KPI kartları */
    .kpi-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-bottom:16px;}}
    .kpi-card{{position:relative;overflow:hidden;background:{t['panel']};border:1px solid {t['border']};border-radius:16px;
      padding:15px 17px;box-shadow:0 4px 16px rgba(0,0,0,.12);transition:transform .15s,box-shadow .15s;}}
    .kpi-card::before{{content:"";position:absolute;left:0;top:0;height:3px;width:100%;background:var(--c);}}
    .kpi-card:hover{{transform:translateY(-3px);box-shadow:0 14px 28px rgba(0,0,0,.22);border-color:{t['acc']};}}
    .kpi-label{{font-size:10px;font-weight:800;color:{t['muted']};letter-spacing:.5px;}}
    .kpi-value{{font-size:25px;font-weight:900;color:{t['text']};margin-top:4px;letter-spacing:-.5px;}}
    .kpi-sub{{font-size:11px;font-weight:700;margin-top:3px;}}

    .panel-ttl{{font-size:13px;font-weight:800;color:{t['ttl']};margin:0 0 10px;display:flex;align-items:center;gap:8px;}}
    .panel-ttl::before{{content:"";width:5px;height:14px;background:linear-gradient({t['acc']},{t['acc2']});border-radius:3px;}}
    [data-testid="stVerticalBlockBorderWrapper"]{{background:{t['panel']};border-radius:16px;
      box-shadow:0 4px 16px rgba(0,0,0,.12);border:1px solid {t['border']} !important;}}

    /* Tablolar */
    table.mx{{width:100%;border-collapse:collapse;font-size:12px;}}
    table.mx th{{color:{t['muted']};font-weight:800;font-size:10px;letter-spacing:.4px;text-align:left;
      padding:8px 10px;border-bottom:2px solid {t['border']};}}
    table.mx td{{padding:9px 10px;border-bottom:1px solid {t['rowb']};color:{t['text']};}}
    table.mx tbody tr:nth-child(even) td, table.mx tr:nth-child(even) td{{background:rgba(255,255,255,.018);}}
    table.mx tr:hover td{{background:{t['rowh']};transition:background .12s ease;}}
    .mx-name{{font-weight:700;color:{t['text']};}}
    .mx-bar{{border-radius:5px;height:17px;line-height:17px;padding-left:7px;font-weight:800;color:#04222b;font-size:9.5px;}}
    .mx-pill{{padding:3px 9px;border-radius:999px;font-weight:800;font-size:9.5px;}}
    .rbar{{display:inline-block;height:7px;background:rgba(251,113,133,.2);border-radius:4px;vertical-align:middle;overflow:hidden;}}
    .rbf{{height:100%;background:#fb7185;border-radius:4px;}}

    div[data-testid="stMetric"]{{background:{t['metricbg']};border:1px solid {t['border']};border-radius:14px;
      padding:13px 16px;box-shadow:0 4px 16px rgba(0,0,0,.12);position:relative;overflow:hidden;
      background-image:linear-gradient(180deg,rgba(34,211,238,.045),transparent);}}
    div[data-testid="stMetric"]::before{{content:"";position:absolute;left:0;top:0;height:3px;width:100%;
      background:linear-gradient(90deg,{t['accd']},{t['acc']});}}
    div[data-testid="stMetric"] *{{color:{t['text']} !important;}}
    div[data-testid="stMetricValue"] *{{color:{t['ttl']} !important;font-weight:900 !important;}}
    div[data-testid="stMetricLabel"] *{{color:{t['muted']} !important;}}

    /* ── NEON KOKPİT (Tasarım 3) ── */
    .neon-title{{font-size:24px;font-weight:900;letter-spacing:2px;color:{t['acc']};
      text-shadow:0 0 18px rgba(34,211,238,.55);margin:0;}}
    .kbox{{border:1px solid {t['border']};border-radius:14px;padding:15px 17px;margin-bottom:12px;
      background:linear-gradient(180deg,rgba(34,211,238,.05),transparent);box-shadow:inset 0 0 22px rgba(34,211,238,.05);}}
    .kbox .kl{{font-size:9.5px;font-weight:800;color:{t['muted']};letter-spacing:1px;}}
    .kbox .kv{{font-size:26px;font-weight:900;margin-top:3px;text-shadow:0 0 14px rgba(34,211,238,.35);}}
    .nchip{{display:inline-block;border:1px solid {t['border']};border-radius:10px;padding:6px 12px;
      margin:2px 5px 0 0;font-size:11.5px;font-weight:800;color:#9fc3e0;}}
    /* Yerel giriş alanlarını koyu temaya uydur */
    [data-testid="stNumberInput"] input, [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea{{
      background:{t['railhov']} !important;color:{t['text']} !important;border:1px solid {t['border']} !important;}}
    [data-testid="stNumberInput"] button{{background:{t['railhov']} !important;color:{t['text']} !important;
      border:1px solid {t['border']} !important;}}
    [data-baseweb="select"] > div{{background:{t['railhov']} !important;border:1px solid {t['border']} !important;
      color:{t['text']} !important;}}
    [data-baseweb="select"] *{{color:{t['text']} !important;}}
    [data-baseweb="popover"] li{{background:{t['panel']} !important;color:{t['text']} !important;}}
    .row-edit{{border-bottom:1px solid {t['rowb']};padding:2px 0;}}
    /* File uploader Türkçeleştirme */
    [data-testid="stFileUploaderDropzoneInstructions"] span{{visibility:hidden;position:relative;}}
    [data-testid="stFileUploaderDropzoneInstructions"] span::after{{
      visibility:visible;position:absolute;left:0;top:0;white-space:nowrap;
      content:"Dosyayı buraya sürükleyin";color:{t['text']};}}
    [data-testid="stFileUploaderDropzoneInstructions"] small{{visibility:hidden;position:relative;}}
    [data-testid="stFileUploaderDropzoneInstructions"] small::after{{
      visibility:visible;position:absolute;left:0;top:0;white-space:nowrap;
      content:"Dosya başına en fazla 10MB";color:{t['muted']};font-size:11px;}}
    [data-testid="stFileUploader"] button{{font-size:0 !important;position:relative;min-width:120px;}}
    [data-testid="stFileUploader"] button::after{{content:"Dosya Seç";font-size:13px;color:{t['text']};
      position:absolute;left:0;right:0;top:50%;transform:translateY(-50%);text-align:center;}}
    /* Butonlar daha okunur ve tıklanabilir hissi */
    .stButton button, .stDownloadButton button, .stFormSubmitButton button{{
      font-weight:600 !important;transition:all .12s ease;}}
    .stButton button:hover, .stDownloadButton button:hover{{
      border-color:{t['acc']} !important;transform:translateY(-1px);}}
    /* Tablo okunabilirlik */
    table.mx{{border-collapse:collapse;width:100%;font-size:11px;}}
    table.mx th{{background:{t['railhov']};color:{t['muted']};font-size:9.5px;letter-spacing:.4px;
      padding:7px 8px;text-transform:uppercase;position:sticky;top:0;border-bottom:2px solid {t['acc']};}}
    table.mx td{{padding:6px 8px;border-bottom:1px solid {t['rowb']};}}
    table.mx tr:hover td{{background:{t['railhov']};}}
    /* Popover (Ekle/Sil) butonları — HER durumda koyu zemin, okunur yazı */
    button[data-testid="stPopoverButton"], button[data-testid="stPopoverButton"] *{{
      background:{t['railhov']} !important;color:{t['text']} !important;border-color:{t['border']} !important;}}
    button[data-testid="stPopoverButton"]:hover, button[data-testid="stPopoverButton"]:hover *{{
      background:{t['panel']} !important;color:{t['acc']} !important;border-color:{t['acc']} !important;}}
    button[data-testid="stPopoverButton"]:focus, button[data-testid="stPopoverButton"]:active,
    button[data-testid="stPopoverButton"][aria-expanded="true"]{{
      background:{t['railhov']} !important;color:{t['text']} !important;border-color:{t['acc']} !important;}}
    button[data-testid="stPopoverButton"][aria-expanded="true"] *{{color:{t['text']} !important;}}
    /* Dropdown (selectbox) — beyaz olmasın, koyu kalsın */
    [data-baseweb="select"] > div, [data-baseweb="select"] > div:hover, [data-baseweb="select"] > div:focus-within{{
      background:{t['railhov']} !important;border:1px solid {t['border']} !important;color:{t['text']} !important;}}
    [data-baseweb="select"] div[aria-selected], [data-baseweb="select"] span, [data-baseweb="select"] div{{
      color:{t['text']} !important;}}
    [data-baseweb="select"] svg{{fill:{t['text']} !important;}}
    /* Açılır liste koyu */
    [data-baseweb="popover"] ul, [data-baseweb="menu"]{{background:{t['panel']} !important;}}
    [data-baseweb="popover"] li, [data-baseweb="menu"] li{{background:{t['panel']} !important;color:{t['text']} !important;}}
    [data-baseweb="popover"] li:hover, [data-baseweb="menu"] li:hover{{background:{t['railhov']} !important;color:{t['acc']} !important;}}
    /* Scrollbar görünür (koyu temaya uygun) — tüm kaydırma alanları */
    ::-webkit-scrollbar{{width:14px;height:14px;}}
    ::-webkit-scrollbar-track{{background:{t['rail']};}}
    ::-webkit-scrollbar-thumb{{background:#3a5169;border-radius:7px;border:3px solid {t['rail']};min-height:40px;}}
    ::-webkit-scrollbar-thumb:hover{{background:{t['acc']};}}
    [data-testid="stMain"]{{scrollbar-color:#3a5169 {t['rail']};scrollbar-width:auto;}}
    [data-testid="stMain"]::-webkit-scrollbar{{width:14px;}}
    [data-testid="stMain"]::-webkit-scrollbar-thumb{{background:#3a5169;border-radius:7px;border:3px solid {t['rail']};}}
    html, body{{scrollbar-color:#3a5169 {t['rail']};}}
    @media (max-width:1250px){{.kpi-grid{{grid-template-columns:repeat(2,1fr);}}}}
    </style>""", unsafe_allow_html=True)


theme = st.session_state.setdefault("theme", "dark")
inject_css(theme)
charts.set_theme(theme)
if not auth.login_gate():
    st.stop()

user = auth.current_user()
ADMIN = auth.is_admin()


@st.cache_resource(show_spinner=False)
def _conn():
    c = storage.get_conn()
    storage.init_db(c)
    return c


conn = _conn()
if "df" not in st.session_state:
    st.session_state.df = storage.load_progress(conn)
if "stock" not in st.session_state:
    st.session_state.stock = storage.load_stock(conn)
if "hse" not in st.session_state:
    st.session_state.hse = storage.load_hse(conn)


def persist_progress():
    storage.save_progress(conn, st.session_state.df)
    # her kayıtta bugünün günlük anlık görüntüsünü güncelle (tüm kapsamlar)
    storage.record_daily(conn, core.per_scope_kpis(core.enrich(st.session_state.df)))


def set_progress(ids, plan=None, real=None, ac=None):
    df = st.session_state.df
    m = df["id"].isin(ids)
    if plan is not None: df.loc[m, "plan"] = max(0.0, min(100.0, float(plan)))
    if real is not None: df.loc[m, "real"] = max(0.0, min(100.0, float(real)))
    if ac is not None:   df.loc[m, "ac"] = max(0.0, float(ac))
    persist_progress()


def add_item(grp, disc, name, unit, qty, up, plan=0.0, real=0.0, ac=0.0):
    df = st.session_state.df
    n = 1
    while f"user_{n}" in set(df["id"]):
        n += 1
    row = {"id": f"user_{n}", "grp": grp, "disc": disc.strip().upper(), "name": name.strip(),
           "unit": unit.strip() or "adet", "qty": float(qty), "up": float(up),
           "plan": max(0.0, min(100.0, float(plan))), "real": max(0.0, min(100.0, float(real))),
           "ac": max(0.0, float(ac))}
    st.session_state.df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    persist_progress()


def delete_items(ids):
    df = st.session_state.df
    st.session_state.df = df[~df["id"].isin(ids)].reset_index(drop=True)
    persist_progress()


meta = {
    "name": storage.get_setting(conn, "proj_name", "ARAKONAK GES"),
    "loc": storage.get_setting(conn, "proj_loc", "Muş / Bulanık"),
    "start": pd.to_datetime(storage.get_setting(conn, "start")),
    "end": pd.to_datetime(storage.get_setting(conn, "end")),
}

# ────────────────────── SOL RAY ──────────────────────
PAGES = ["Komuta Paneli", "İş Programına Göre İlerleme", "Hakedişe Esas İmalat",
         "Stok Durumu", "Rapor & Yedek", "Ayarlar"]
ICON = {"Komuta Paneli": "▦", "İş Programına Göre İlerleme": "📅", "Hakedişe Esas İmalat": "🏗",
        "Stok Durumu": "📦", "Rapor & Yedek": "⭳", "Ayarlar": "⚙"}
with st.sidebar:
    _logo_b64 = LOGO_WHITE if theme == "dark" else LOGO_BLACK
    if _logo_b64:
        st.markdown(f'<div class="rail-logo"><img src="data:image/svg+xml;base64,{_logo_b64}"/></div>',
                    unsafe_allow_html=True)
    page = st.radio("Menü", PAGES, label_visibility="collapsed")

    st.markdown('<div class="rail-sec">TEMA</div>', unsafe_allow_html=True)
    light_on = st.toggle("☀️ Açık tema", value=(theme == "light"), key="light_toggle")
    want = "light" if light_on else "dark"
    if want != theme:
        st.session_state.theme = want
        st.rerun()

    st.markdown(f'<div class="rail-user">👤 <b>{user["name"]}</b><br>'
                f'<span style="opacity:.7">{user["username"]} · {user["role"]}</span></div>',
                unsafe_allow_html=True)
    if st.button("Çıkış yap", width="stretch"):
        auth.logout(); st.rerun()
    if ADMIN:
        if st.button("↺ Verileri sıfırla", width="stretch"):
            storage.reset_all(conn)
            for kk in ("df", "stock", "hse"):
                st.session_state.pop(kk, None)
            for kk in [x for x in list(st.session_state.keys())
                       if str(x).startswith(("ep_", "er_", "ea_"))]:
                st.session_state.pop(kk, None)
            st.rerun()

# ────────────────────── ÜST BAŞLIK ──────────────────────
head_l, head_r = st.columns([2.2, 1.4])
with head_l:
    st.markdown(f"""<div class="pagehd"><div>
      <h1>{page}</h1>
      <div class="sub">{meta['name']} · Canlı EPC İlerleme &amp; Bütçe · {date.today().strftime('%d.%m.%Y')}</div>
    </div></div>""", unsafe_allow_html=True)
scope_label = "Tümü"
scope = "ALL"

base = core.enrich(st.session_state.df)
scoped = core.scope_df(base, scope)
k = core.kpis(scoped)


# ────────────────────── ORTAK PARÇALAR ──────────────────────
def kpi_ribbon():
    spi = "—" if k["SPI"] is None else f"{k['SPI']:.2f}"
    if k["SPI"] is None:
        sc, sd = MUTED, "veri yok"
    elif k["SPI"] >= 1:
        sc, sd = TEAL_D, "▲ planında"
    else:
        sc, sd = RED, "▼ hedef altı"
    st.markdown(f"""
    <div class="kpi-grid">
      <div class="kpi-card" style="--c:linear-gradient(90deg,#22d3ee,#2dd4bf)">
        <div class="kpi-label">TOPLAM BÜTÇE (BAC)</div><div class="kpi-value">{core.fmt_money(k['budget'])}</div>
        <div class="kpi-sub" style="color:#8aa">Sözleşme bedeli</div></div>
      <div class="kpi-card" style="--c:linear-gradient(90deg,{TEAL},#14b8a6)">
        <div class="kpi-label">KAZANILAN</div><div class="kpi-value" style="color:{TEAL}">{core.fmt_money(k['comp'])}</div>
        <div class="kpi-sub" style="color:{TEAL}">▲ %{k['ilerleme']:.1f}</div></div>
      <div class="kpi-card" style="--c:linear-gradient(90deg,#0e7490,#14b8a6)">
        <div class="kpi-label">PLANA GÖRE</div><div class="kpi-value">%{k['planPct']:.1f}</div>
        <div class="kpi-sub" style="color:{AMBER}">{abs(k['ilerleme']-k['planPct']):.0f} puan {'geride' if k['ilerleme']<k['planPct'] else 'önde'}</div></div>
      <div class="kpi-card" style="--c:linear-gradient(90deg,{AMBER},#f59e0b)">
        <div class="kpi-label">SPI · ZAMAN PERF.</div><div class="kpi-value" style="color:{sc}">{spi}</div>
        <div class="kpi-sub" style="color:{sc}">{sd}</div></div>
      <div class="kpi-card" style="--c:linear-gradient(90deg,#fb7185,{RED})">
        <div class="kpi-label">KALAN İŞ</div><div class="kpi-value">{core.fmt_money(k['kalan'])}</div>
        <div class="kpi-sub" style="color:#8aa">Bakiye</div></div>
    </div>""", unsafe_allow_html=True)


def gran_buttons(key: str, default: str = "Günlük") -> str:
    """Grafik üstünde Günlük / Haftalık / Aylık seçim butonları. Seçili granülariteyi döndürür."""
    sk = f"gran_{key}"
    if sk not in st.session_state:
        st.session_state[sk] = default
    cols = st.columns([1, 1, 1, 5])
    for i, lb in enumerate(["Günlük", "Haftalık", "Aylık"]):
        typ = "primary" if st.session_state[sk] == lb else "secondary"
        if cols[i].button(lb, key=f"{sk}_{lb}", type=typ, use_container_width=True):
            st.session_state[sk] = lb
            st.rerun()
    return st.session_state[sk]


def items_table_html(view: pd.DataFrame, limit: int = 400):
    rows = ""
    for _, r in view.head(limit).iterrows():
        rl = r["real"]; col = TEAL if rl >= r["plan"] else RED
        w = max(0, min(100, rl))
        dcol = {"TAMAMLANDI": TEAL, "DEVAM": "#38bdf8", "GERİDE": RED, "BAŞLAMADI": "#5f7a99"}.get(r["durum"], "#5f7a99")
        rows += (f'<tr><td class="mx-name" style="max-width:340px">{r["name"][:70]}</td>'
                 f'<td style="color:#5f7a99;font-size:10px">{r["disc"][:16]}</td>'
                 f'<td style="text-align:right;color:#9fc3e0;font-size:10.5px">{r["qty"]:,.0f}</td>'
                 f'<td style="color:#7fb0b3;font-size:10px">{r["unit"]}</td>'
                 f'<td style="text-align:right;color:#9fc3e0;font-size:10.5px">${r["up"]:,.2f}</td>'
                 f'<td style="text-align:right;color:#c7e8e4;font-size:10.5px">{core.fmt_money(r["tutar"])}</td>'
                 f'<td style="text-align:center;color:#5f7a99">%{r["plan"]:.0f}</td>'
                 f'<td style="min-width:110px"><div style="position:relative;background:#0e2233;border-radius:5px;'
                 f'height:16px;overflow:hidden"><div style="position:absolute;left:0;top:0;height:100%;width:{w:.0f}%;'
                 f'background:{col};border-radius:5px"></div><span style="position:absolute;left:7px;top:0;line-height:16px;'
                 f'font-size:9.5px;font-weight:800;color:#e8f4ff">%{rl:.0f}</span></div></td>'
                 f'<td style="text-align:center"><span style="color:{dcol};font-weight:800;font-size:10px">{r["durum"]}</span></td></tr>')
    st.markdown(f"""<table class="mx"><tr>
      <th>POZ ADI</th><th>DİSİPLİN/GRUP</th><th style="text-align:right">MİKTAR</th><th>BİRİM</th>
      <th style="text-align:right">BİRİM FİYAT</th><th style="text-align:right">TUTAR</th>
      <th style="text-align:center">PLAN %</th><th>GERÇEK %</th><th style="text-align:center">DURUM</th></tr>
      {rows}</table>""", unsafe_allow_html=True)


def matrix_table(g: pd.DataFrame):
    rows = ""
    for _, r in g.sort_values("budget", ascending=False).iterrows():
        rl, pl, sp = r["realPct"], r["planPct"], r["sapma"]
        col = TEAL if rl >= pl else RED
        if sp >= 0:
            pill_bg, pill_c, pill_t = "rgba(52,211,153,.15)", GREEN, "İYİ"
        elif sp >= -6:
            pill_bg, pill_c, pill_t = "rgba(251,191,36,.15)", AMBER, "İZLE"
        else:
            pill_bg, pill_c, pill_t = "rgba(251,113,133,.15)", RED, "RİSK"
        w = max(0, min(100, rl))
        rows += (f'<tr><td class="mx-name">{r["disc"]}</td>'
                 f'<td style="text-align:right;color:#9fc3e0;font-weight:700">{core.fmt_money(r["budget"])}</td>'
                 f'<td style="text-align:center;color:#5f7a99">%{pl:.0f}</td>'
                 f'<td style="min-width:170px"><div style="position:relative;background:#0e2233;border-radius:5px;'
                 f'height:18px;overflow:hidden"><div style="position:absolute;left:0;top:0;height:100%;width:{w:.0f}%;'
                 f'background:{col};border-radius:5px"></div><span style="position:absolute;left:8px;top:0;line-height:18px;'
                 f'font-size:10px;font-weight:800;color:#e8f4ff">%{rl:.0f}</span></div></td>'
                 f'<td style="text-align:center;font-weight:800;color:{col}">{sp:+.0f}</td>'
                 f'<td style="text-align:center"><span class="mx-pill" style="background:{pill_bg};color:{pill_c}">{pill_t}</span></td></tr>')
    st.markdown(f"""<table class="mx"><tr>
      <th>DİSİPLİN</th><th style="text-align:right">BÜTÇE</th><th style="text-align:center">PLAN %</th>
      <th>GERÇEK %</th><th style="text-align:center">SAPMA</th><th style="text-align:center">DURUM</th></tr>
      {rows}</table>""", unsafe_allow_html=True)


PLOT = {"displayModeBar": False}


def risk_table(dl: pd.DataFrame):
    if dl is None or dl.empty:
        st.markdown('<div style="color:#7e93b0;font-size:12px;padding:10px 0">Geride kalan kritik iş yok. 🎉</div>',
                    unsafe_allow_html=True)
        return
    mx = float(dl["riskUSD"].max()) or 1.0
    rows = ""
    for _, r in dl.head(7).iterrows():
        w = max(8, r["riskUSD"] / mx * 100)
        nm = r["name"] if len(r["name"]) <= 46 else r["name"][:44] + "…"
        rows += (f'<tr><td style="width:58%;color:#d5e6f7;font-size:11px">{nm}</td>'
                 f'<td style="width:28%"><span class="rbar" style="width:100%"><span class="rbf" style="width:{w:.0f}%;display:block"></span></span></td>'
                 f'<td style="width:14%;text-align:right;font-weight:800;color:#fca5b5;font-size:11px">{core.fmt_money(r["riskUSD"])}</td></tr>')
    st.markdown(f'<table class="mx" style="width:100%">{rows}</table>', unsafe_allow_html=True)


# ══════════════════════ SAYFALAR ══════════════════════
if page == "Komuta Paneli":
    g = core.disc_agg(base, scope)
    gag = core.group_agg(base)
    snaps_items = core.s_curve_from_snapshots(storage.load_snapshots(conn, scope))
    _plan = storage.load_table(conn, "planline", core.month_rows(meta["start"], meta["end"]))
    _bm, _ = core.manual_curve(_plan, k["BAC"])
    baseline = _bm            # plan = yalnızca elle girilen Plan Programı
    snaps = snaps_items       # gerçek = İş Kalemleri verisi
    spi = "—" if k["SPI"] is None else f"{k['SPI']:.2f}"
    spi_arrow = "" if k["SPI"] is None else ("▲" if k["SPI"] >= 1 else "▼")
    spi_col = MUTED if k["SPI"] is None else (TEAL if k["SPI"] >= 1 else RED)

    # Üst şerit: Toplam Bütçe · Kazanılan (EV) · Kalan İş — YÜKLENİCİ HAKEDİŞ bedelinden ($10.25M)
    _oz_strip = core.maliyet_ozet(base)
    _bac_y = _oz_strip["bac"]
    _ev_y = _oz_strip["ev"]
    _kalan_y = _oz_strip["kalan"]
    st.markdown(
        f'<div style="display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap">'
        f'<div style="flex:1;min-width:200px;background:rgba(56,189,248,.08);border:1px solid #123a44;'
        f'border-radius:10px;padding:11px 16px"><span style="color:#38bdf8;font-size:10.5px;font-weight:700;letter-spacing:.5px">TOPLAM BÜTÇE</span>'
        f'<div style="color:#e6f4f4;font-size:20px;font-weight:800">{core.fmt_money(_bac_y)}</div></div>'
        f'<div style="flex:1;min-width:200px;background:rgba(34,211,238,.08);border:1px solid #123a44;'
        f'border-radius:10px;padding:11px 16px"><span style="color:#22d3ee;font-size:10.5px;font-weight:700;letter-spacing:.5px">KAZANILAN</span>'
        f'<div style="color:#e6f4f4;font-size:20px;font-weight:800">{core.fmt_money(_ev_y)}</div></div>'
        f'<div style="flex:1;min-width:200px;background:rgba(251,113,133,.08);border:1px solid #402028;'
        f'border-radius:10px;padding:11px 16px"><span style="color:#fb7185;font-size:10.5px;font-weight:700;letter-spacing:.5px">KALAN İŞ</span>'
        f'<div style="color:#e6f4f4;font-size:20px;font-weight:800">{core.fmt_money(_kalan_y)}</div></div>'
        f'</div>', unsafe_allow_html=True)

    hero = st.columns([1, 1.15], gap="medium")
    with hero[0]:
        with st.container(border=True):
            st.markdown('<div class="panel-ttl">Genel Fiziki İlerleme</div>', unsafe_allow_html=True)
            st.plotly_chart(charts.progress_donut(k["ilerleme"], k["planPct"]),
                            width="stretch", config=PLOT)
    with hero[1]:
        with st.container(border=True):
            st.markdown('<div class="panel-ttl">İşin Fiziki İlerlemesi — GES-1 / GES-2 / ORTAK</div>', unsafe_allow_html=True)
            _ges = core.maliyet_ges_progress(base)
            st.plotly_chart(charts.group_gauges(_ges), width="stretch", config=PLOT, key="ges_fiziki")

    with st.container(border=True):
        _hak = core.hakedis_pursantaj(base)
        _ozp = core.maliyet_ozet(base)
        cc = st.columns(2)
        cc[0].metric("Fiziki İlerleme (saha)", f"%{_ozp['ilerleme']:.1f}", help="Birim fiyat cetveli · tutar-ağırlıklı")
        cc[1].metric("Hakediş (pursantaj)", f"%{_hak['hakedis_pct']:.2f}", help="Ödemeye esas pursantaj")


    # Hakedişe esas imalat — grup bazında (yüklenici tek poz kullandığı için GES bölünmez)
    with st.container(border=True):
        st.markdown('<div class="panel-ttl">Kümülatif S-Eğrisi</div>', unsafe_allow_html=True)
        gran = gran_buttons("dash_scurve")
        snaps_g = core.scurve_series_gran(storage.load_snapshots(conn, scope), gran)
        snaps_use = snaps_g if not snaps_g.empty else snaps
        st.plotly_chart(charts.s_curve(baseline, snaps_use, k["planPct"], k["ilerleme"],
                                       xstart=meta["start"], xend=meta["end"]),
                        width="stretch", config=PLOT)
        with st.expander("📅 Plan Programı — aylık planlanan % (plan çizgisini buradan çizin)"):
            _pl_default = [{"Ay": r["Ay"], "Plan %": r["Plan %"]} for r in core.month_rows(meta["start"], meta["end"])]
            _planline = storage.load_table(conn, "planline", _pl_default)
            if "Gerçek %" in _planline.columns:
                _planline = _planline.drop(columns=["Gerçek %"])
            _pl_ed = st.data_editor(_planline, width="stretch", hide_index=True, num_rows="dynamic",
                                    disabled=not ADMIN, key="planline_ed",
                                    column_config={
                                        "Ay": st.column_config.TextColumn("Ay (YYYY-AA)"),
                                        "Plan %": st.column_config.NumberColumn("Plan % (kümülatif hedef)",
                                                                                min_value=0, max_value=100, step=1)})
            if ADMIN and not _pl_ed.equals(_planline):
                storage.save_table(conn, "planline", _pl_ed); st.rerun()

elif page == "İş Programına Göre İlerleme":
    st.markdown('<div style="background:linear-gradient(90deg,rgba(34,211,238,.10),rgba(139,92,246,.06));'
                'border:1px solid #12324a;border-radius:12px;padding:11px 16px;font-size:12.5px;'
                'color:#cfe3f7;margin-bottom:14px">📅 <b>İş Programına Göre İlerleme:</b> '
                'Birim fiyat cetvelindeki 122 kalem (GES-1/GES-2/ORTAK ayrımlı · $10.25M). '
                'Her kaleme <b>Plan %</b> ve <b>Gerçek %</b> girin — Komuta Paneli\'ndeki GES göstergeleri, '
                'fiziki ilerleme ve hakediş (pursantaj) buradan beslenir.</div>',
                unsafe_allow_html=True)
    kpi_ribbon()

    # Filtreler
    f1, f2, f3 = st.columns([1.4, 1.4, 1.4])
    grp_view = f1.selectbox("Grup", ["(Tümü)"] + sorted(base["grp"].unique().tolist()), index=0)
    search = f3.text_input("🔎 Poz adında ara", "")
    view = base if grp_view == "(Tümü)" else base[base["grp"] == grp_view]
    if search.strip():
        view = view[view["name"].str.contains(search.strip(), case=False, na=False)]
    view = view.sort_values("tutar", ascending=False)  # en büyük tutar üstte

    # Düzenleme modu + Ekle/Sil aynı satırda
    edit_mode = False
    if ADMIN:
        tcol, acol, dcol = st.columns([2, 1.3, 1.3])
        edit_mode = tcol.toggle("✏️ Düzenleme modu", value=False,
                                help="Açıkken her kalem düzenlenip yanındaki 💾 ile tek tek kaydedilir.")
        with acol:
            with st.popover("➕ Yeni İş Kalemi Ekle", use_container_width=True):
                with st.form("add_item_form", clear_on_submit=True):
                    ai_grp = st.selectbox("Grup", sorted(base["grp"].unique().tolist()))
                    disc_opts = sorted(base["disc"].unique().tolist())
                    ai_disc = st.selectbox("Disiplin", disc_opts + ["➕ Yeni disiplin…"])
                    ai_disc_new = st.text_input("Yeni disiplin adı", "")
                    ai_name = st.text_input("Poz Adı", "")
                    b1, b2, b3 = st.columns(3)
                    ai_unit = b1.text_input("Birim", "adet")
                    ai_qty = b2.number_input("Miktar", min_value=0.0, value=1.0, step=1.0)
                    ai_up = b3.number_input("Birim Fiyat ($)", min_value=0.0, value=0.0, step=100.0)
                    c1, c2 = st.columns(2)
                    ai_plan = c1.number_input("Plan %", 0, 100, 0)
                    ai_real = c2.number_input("Gerçek %", 0, 100, 0)
                    submitted = st.form_submit_button("➕ Ekle", type="primary", width="stretch")
                if submitted:
                    disc_final = ai_disc_new.strip() if ai_disc == "➕ Yeni disiplin…" else ai_disc
                    if not ai_name.strip() or not disc_final:
                        st.error("Poz adı ve disiplin zorunlu.")
                    else:
                        add_item(ai_grp, disc_final, ai_name, ai_unit, ai_qty, ai_up, ai_plan, ai_real)
                        st.toast("Yeni iş kalemi eklendi."); st.rerun()
        with dcol:
            with st.popover("🗑 İş Kalemi Sil", use_container_width=True):
                del_map = {f'{r["disc"]} — {r["name"][:50]}': r["id"] for _, r in scoped.iterrows()}
                del_sel = st.multiselect("Silinecek kalem(ler)", list(del_map.keys()))
                if st.button("Seçilenleri sil", disabled=not del_sel, width="stretch"):
                    delete_items([del_map[x] for x in del_sel])
                    st.toast(f"{len(del_sel)} kalem silindi."); st.rerun()

    st.markdown(f'<div style="color:#7fb0b3;font-size:12px;margin:6px 0">Görüntülenen: '
                f'<b>{len(view)}</b> kalem · Toplam <b>{core.fmt_money(view["tutar"].sum())}</b></div>',
                unsafe_allow_html=True)

    if ADMIN and edit_mode and len(view) > 0:
        PAGE = 40
        total = len(view)
        sl = view
        if total > PAGE:
            pages = (total + PAGE - 1) // PAGE
            pg = st.number_input(f"Sayfa (her sayfada {PAGE} kalem · toplam {pages} sayfa)",
                                 min_value=1, max_value=pages, value=1, step=1)
            sl = view.iloc[(pg - 1) * PAGE: pg * PAGE]
            st.caption(f"{(pg-1)*PAGE+1}–{min(pg*PAGE, total)} arası kalemler gösteriliyor.")
        # başlık satırı
        h = st.columns([2.8, 1.0, 0.9, 1.2, 1.0, 1.0, 0.8])
        h[0].markdown("**Poz Adı**"); h[1].markdown("**Miktar**"); h[2].markdown("**Grup**")
        h[3].markdown("**Tutar**")
        h[4].markdown("**Plan %**"); h[5].markdown("**Gerçek %**"); h[6].markdown("**Kaydet**")
        _gcol = {"GES-1": "#22d3ee", "GES-2": "#34d399", "ORTAK": "#a78bfa"}
        for _, r in sl.iterrows():
            rid = r["id"]
            st.session_state.setdefault(f"ep_{rid}", int(round(r["plan"])))
            st.session_state.setdefault(f"er_{rid}", int(round(r["real"])))
            c = st.columns([2.8, 1.0, 0.9, 1.2, 1.0, 1.0, 0.8])
            c[0].markdown(f'<div style="font-size:11px;padding-top:8px;color:#dbeafe">{r["name"][:48]}</div>', unsafe_allow_html=True)
            c[1].markdown(f'<div style="font-size:11px;padding-top:8px;color:#9fc3e0;text-align:right">{r["qty"]:,.0f} {r["unit"]}</div>', unsafe_allow_html=True)
            c[2].markdown(f'<div style="font-size:11px;padding-top:8px;font-weight:700;color:{_gcol.get(r["grp"], "#7fb0b3")}">{str(r["grp"])[:10]}</div>', unsafe_allow_html=True)
            c[3].markdown(f'<div style="font-size:11px;padding-top:8px;color:#c7e8e4;text-align:right">{core.fmt_money(r["tutar"])}</div>', unsafe_allow_html=True)
            c[4].number_input("p", 0, 100, key=f"ep_{rid}", label_visibility="collapsed")
            c[5].number_input("r", 0, 100, key=f"er_{rid}", label_visibility="collapsed")
            if c[6].button("💾", key=f"save_{rid}", help="Bu kalemi kaydet"):
                old = st.session_state.df.set_index("id").loc[rid]
                nm = str(old["name"])[:40]
                p = max(0.0, min(100.0, float(st.session_state.get(f"ep_{rid}", old["plan"]))))
                rl = max(0.0, min(100.0, float(st.session_state.get(f"er_{rid}", old["real"]))))
                changed = False
                if abs(p - float(old["plan"])) > 1e-9:
                    storage.log_change(conn, user["username"], nm, "Plan %", f"{old['plan']:.0f}", f"{p:.0f}"); changed = True
                if abs(rl - float(old["real"])) > 1e-9:
                    storage.log_change(conn, user["username"], nm, "Gerçek %", f"{old['real']:.0f}", f"{rl:.0f}"); changed = True
                if changed:
                    st.session_state.df.loc[st.session_state.df["id"] == rid, ["plan", "real"]] = [p, rl]
                    persist_progress()
                    st.toast(f"✅ Kaydedildi: {nm}")
                    st.rerun()
                else:
                    st.toast("Değişiklik yok.")
    elif not (ADMIN and edit_mode):
        items_table_html(view)


elif page == "Hakedişe Esas İmalat":
    st.markdown('<div style="background:linear-gradient(90deg,rgba(52,211,153,.10),rgba(34,211,238,.05));'
                'border:1px solid #12324a;border-radius:12px;padding:11px 16px;font-size:12.5px;'
                'color:#cfe3f7;margin-bottom:14px">🏗 <b>Hakedişe Esas İmalat (Pursantaj):</b> '
                'Ödemeye esas pursantaja göre hak edilen tutar. İlerleme İş Programına Göre İlerleme '
                'sayfasından gelir; her kalemin pursantaj ağırlığıyla hakediş hesaplanır.</div>',
                unsafe_allow_html=True)
    _md = core.maliyet_enrich(base)
    _hak = core.hakedis_pursantaj(base)
    _ozh = core.maliyet_ozet(base)
    _bac = _ozh["bac"]
    _hak_tutar = _bac * _hak["hakedis_pct"] / 100
    _kalan_hak = _bac - _hak_tutar

    hero = st.columns([1.15, 1], gap="medium")
    with hero[0]:
        with st.container(border=True):
            st.markdown('<div class="panel-ttl">Hakediş İlerlemesi (Pursantaj)</div>', unsafe_allow_html=True)
            st.plotly_chart(charts.hakedis_donut(_hak_tutar, _kalan_hak, _bac),
                            width="stretch", config=PLOT, key="hakedis_donut")
            st.caption("Yeşil = hak edilen (pursantaj) · koyu = kalan. Fiziki ilerlemeden farklı olabilir.")
    with hero[1]:
        st.markdown(f"""
        <div class="kbox"><div class="kl">SÖZLEŞME BEDELİ (BAC)</div>
          <div class="kv" style="color:#38bdf8">{core.fmt_money(_bac)}</div></div>
        <div class="kbox"><div class="kl">HAK EDİLEN (PURSANTAJ)</div>
          <div class="kv" style="color:#34d399">{core.fmt_money(_hak_tutar)}</div></div>
        <div class="kbox"><div class="kl">KALAN HAKEDİŞ</div>
          <div class="kv" style="color:#fb7185">{core.fmt_money(_kalan_hak)}</div></div>
        <div class="kbox"><div class="kl">HAKEDİŞ İLERLEMESİ</div>
          <div class="kv" style="color:#22d3ee">%{_hak["hakedis_pct"]:.2f}</div></div>
        """, unsafe_allow_html=True)

    _fiz = _ozh["ilerleme"]
    _hkp = _hak["hakedis_pct"]
    st.markdown(f'<div style="background:rgba(34,211,238,.06);border:1px solid #12324a;border-radius:10px;'
                f'padding:9px 14px;font-size:12px;color:#cfe3f7;margin:4px 0 12px">ℹ️ '
                f'<b>Fiziki (saha):</b> %{_fiz:.1f} · <b>Hakediş (ödeme):</b> %{_hkp:.2f} · '
                f'Fark: {_hkp-_fiz:+.1f} puan. Fiziki = birim fiyat, hakediş = pursantaj — farklı olması normaldir.</div>',
                unsafe_allow_html=True)

    f1, f2, f3 = st.columns([1.4, 1.4, 1])
    disc_view = f1.selectbox("Disiplin", ["(Tümü)"] + sorted(_md["disc"].unique().tolist()), key="hk_disc")
    ara = f2.text_input("Poz adında ara", key="hk_ara", placeholder="ör. panel, kablo...")
    view = _md if disc_view == "(Tümü)" else _md[_md["disc"] == disc_view]
    if ara and "name" in view.columns:
        view = view[view["name"].str.contains(ara, case=False, na=False)]
    view = view.sort_values("pursantaj", ascending=False)
    _he_tutar = float((view["pursantaj"] * view["real"] / 100).sum() * _bac)
    st.caption(("Görüntülenen: %d kalem · Hak edilen %s" % (len(view), core.fmt_money(_he_tutar))).replace("$", "\\$"))

    edit_mode = f3.toggle("✏️ Düzenleme modu", value=False, key="hk_edit") if ADMIN else False
    import data_maliyet as _dm
    _admap = {r["poz"]: r["ad"] for r in _dm.MALIYET}

    PAGE = 40
    pages_n = max(1, (len(view) + PAGE - 1) // PAGE)
    pg = st.number_input(f"Sayfa (her sayfada {PAGE} kalem · toplam {pages_n} sayfa)", 1, pages_n, 1, key="hk_pg") if len(view) > PAGE else 1
    sl = view.iloc[(pg - 1) * PAGE: pg * PAGE]

    if edit_mode:
        for _, r in sl.iterrows():
            st.session_state.setdefault(f"hr_{r['id']}", int(round(r["real"])))
        h = st.columns([2.8, 1.1, 0.9, 1.1, 1.1, 0.8])
        h[0].markdown("**Kalem**"); h[1].markdown("**Pursantaj**"); h[2].markdown("**Gerçek %**")
        h[3].markdown("**Hak Edilen %**"); h[4].markdown("**Tutar**"); h[5].markdown("**Kaydet**")
        for _, r in sl.iterrows():
            rid = r["id"]; ad = _admap.get(rid, rid); purs = r["pursantaj"] * 100
            real = st.session_state.get(f"hr_{rid}", r["real"])
            hak_purs = purs * real / 100
            cc = st.columns([2.8, 1.1, 0.9, 1.1, 1.1, 0.8])
            cc[0].markdown(f'<div style="font-size:11px;padding-top:8px;color:#dbeafe">{str(ad)[:50]}</div>', unsafe_allow_html=True)
            cc[1].markdown(f'<div style="font-size:11px;padding-top:8px;color:#a78bfa;text-align:right">%{purs:.3f}</div>', unsafe_allow_html=True)
            cc[2].number_input("r", 0, 100, key=f"hr_{rid}", label_visibility="collapsed")
            cc[3].markdown(f'<div style="font-size:11px;padding-top:8px;color:#34d399;text-align:right">%{hak_purs:.3f}</div>', unsafe_allow_html=True)
            cc[4].markdown(f'<div style="font-size:11px;padding-top:8px;color:#c7e8e4;text-align:right">{core.fmt_money(r["tutar"])}</div>', unsafe_allow_html=True)
            if cc[5].button("💾", key=f"hksave_{rid}", help="Bu kalemi kaydet"):
                rl = max(0.0, min(100.0, float(st.session_state.get(f"hr_{rid}", 0))))
                st.session_state.df.loc[st.session_state.df["id"] == rid, "real"] = rl
                persist_progress()
                st.toast(f"✅ Kaydedildi: {str(ad)[:30]}")
                st.rerun()
        st.caption("💡 Buradaki Gerçek % İş Programına Göre İlerleme ile aynı veridir — birinde değişince diğeri de güncellenir.")
    else:
        rows = ""
        for _, r in sl.iterrows():
            pid = r["id"]; ad = _admap.get(pid, pid)
            purs = r["pursantaj"] * 100; real = r["real"]; hak_purs = purs * real / 100
            rows += ('<tr><td style="color:#5f7a99;font-size:10px">' + str(pid) + '</td>'
                     '<td class="mx-name" style="font-size:11px;max-width:320px">' + str(ad)[:60] + '</td>'
                     '<td style="text-align:right;color:#a78bfa;font-size:10.5px">%' + ("%.3f" % purs) + '</td>'
                     '<td style="text-align:center;color:#22d3ee;font-size:10.5px">%' + ("%.0f" % real) + '</td>'
                     '<td style="text-align:right;color:#34d399;font-size:10.5px">%' + ("%.3f" % hak_purs) + '</td>'
                     '<td style="text-align:right;color:#c7e8e4;font-size:10.5px">' + core.fmt_money(r["tutar"]) + '</td></tr>')
        st.markdown('<table class="mx"><tr><th>POZ</th><th>KALEM</th><th style="text-align:right">PURSANTAJ</th>'
                    '<th>GERÇEK %</th><th style="text-align:right">HAK EDİLEN %</th>'
                    '<th style="text-align:right">TUTAR</th></tr>' + rows + '</table>', unsafe_allow_html=True)


elif page == "Stok Durumu":
    st.markdown('<div style="background:linear-gradient(90deg,rgba(251,191,36,.10),rgba(52,211,153,.05));'
                'border:1px solid #12324a;border-radius:12px;padding:11px 16px;font-size:12.5px;'
                'color:#cfe3f7;margin-bottom:14px">📦 <b>Stok Durumu (sorumluluk bazlı):</b> '
                '<span style="color:#fbbf24">İşveren</span> kalemlerinde: Depoya Gelen → Yükleniciye Verilen → İmalata Giren '
                '(depoda kalan + yüklenicide bekleyen ayrı hesaplanır). '
                '<span style="color:#22d3ee">Yüklenici</span> kalemlerinde: sadece Sahada İmalata Giren.</div>',
                unsafe_allow_html=True)
    stok = storage.load_stok(conn)
    se = core.stok_enrich(stok)
    oz = core.stok_ozet(stok)

    # Üstte GES-1/GES-2/ORTAK genel grafik (ana ilerlemeden)
    with st.container(border=True):
        st.markdown('<div class="panel-ttl">GES-1 / GES-2 / ORTAK İlerleme</div>', unsafe_allow_html=True)
        _ges = core.maliyet_ges_progress(base)
        st.plotly_chart(charts.group_gauges(_ges), width="stretch", config=PLOT, key="ges_stok")

    c = st.columns(4)
    c[0].metric("İşveren Teslim Değeri", core.fmt_money(oz["gelen_deger"]),
                help="İşverenin tedarik edip depoya aldığı malzeme değeri")
    c[1].metric("Depoda Bekleyen", core.fmt_money(oz["depoda_deger"]),
                help="İşveren deposunda, henüz yükleniciye verilmemiş")
    c[2].metric("Yüklenicide Bekleyen", core.fmt_money(oz["yuklenicide_deger"]),
                help="Yükleniciye verilmiş ama henüz imalata girmemiş")
    c[3].metric("Sahada İmalat (esas)", core.fmt_money(oz["hakedise_esas"]))
    if oz["mutabakatsiz"] > 0:
        st.markdown(f'<div style="background:rgba(251,113,133,.12);border:1px solid #fb7185;border-radius:10px;'
                    f'padding:9px 13px;font-size:12px;color:#fecdd3;margin:6px 0 10px">🔴 <b>Mutabakatsızlık:</b> '
                    f'{oz["mutabakatsiz"]} kalemde imalat > verilen veya verilen > gelen. Kontrol edin.</div>', unsafe_allow_html=True)

    f1, f2, f3 = st.columns([1.3, 1.3, 1.2])
    sor_view = f1.selectbox("Sorumluluk", ["(Tümü)", "İşveren", "Yüklenici"], key="st_sor")
    ara = f2.text_input("Malzeme adında ara", key="st_ara", placeholder="ör. panel...")
    only_isv = f3.checkbox("Sadece stoklu (işveren)", value=False, key="st_only")
    view = se if sor_view == "(Tümü)" else se[se["sorumluluk"] == sor_view]
    if ara:
        view = view[view["ad"].str.contains(ara, case=False, na=False)]
    if only_isv:
        view = view[view["kalan_stok"] > 0]
    view = view.sort_values("tutar", ascending=False)  # en büyük tutar üstte
    st.caption(f"Görüntülenen: {len(view)} kalem · İşveren stok değeri {core.fmt_money(view['stok_deger'].sum())}".replace("$", "\\$"))

    edit_mode = st.toggle("✏️ Düzenleme modu", value=False, key="st_edit") if ADMIN else False
    PAGE = 40
    pages_n = max(1, (len(view) + PAGE - 1) // PAGE)
    pg = st.number_input(f"Sayfa (her sayfada {PAGE} kalem · toplam {pages_n} sayfa)", 1, pages_n, 1, key="st_pg") if len(view) > PAGE else 1
    sl = view.iloc[(pg - 1) * PAGE: pg * PAGE]

    if edit_mode:
        for _, r in sl.iterrows():
            st.session_state.setdefault(f"sg_{r['poz']}", float(r["gelen"]))
            st.session_state.setdefault(f"sv_{r['poz']}", float(r["veren"]))
            st.session_state.setdefault(f"si_{r['poz']}", float(r["imalat"]))
        h = st.columns([2.4, 0.8, 0.9, 1.15, 1.15, 1.15, 1.15, 0.7])
        h[0].markdown("**Malzeme**"); h[1].markdown("**Sorumlu**"); h[2].markdown("**Sözleşme**")
        h[3].markdown("**Depoya Gelen**"); h[4].markdown("**Yük.'ye Verilen**"); h[5].markdown("**İmalata Giren**")
        h[6].markdown("**Kalan**"); h[7].markdown("**💾**")
        for _, r in sl.iterrows():
            poz = r["poz"]; is_isv = r["sorumluluk"] == "İşveren"
            gelen = st.session_state.get(f"sg_{poz}", r["gelen"])
            veren = st.session_state.get(f"sv_{poz}", r["veren"])
            imalat = st.session_state.get(f"si_{poz}", r["imalat"])
            cc = st.columns([2.4, 0.8, 0.9, 1.15, 1.15, 1.15, 1.15, 0.7])
            cc[0].markdown(f'<div style="font-size:11px;padding-top:8px;color:#dbeafe">{r["ad"][:42]}</div>', unsafe_allow_html=True)
            _scol = "#fbbf24" if is_isv else "#22d3ee"
            cc[1].markdown(f'<div style="font-size:10px;padding-top:9px;font-weight:700;color:{_scol}">{"İşv" if is_isv else "Yük"}</div>', unsafe_allow_html=True)
            cc[2].markdown(f'<div style="font-size:11px;padding-top:8px;color:#9fc3e0;text-align:right">{r["miktar"]:,.0f}</div>', unsafe_allow_html=True)
            if is_isv:
                # İşveren: 3 giriş (gelen, veren, imalat)
                cc[3].number_input("g", min_value=0.0, step=100.0, key=f"sg_{poz}", label_visibility="collapsed")
                cc[4].number_input("v", min_value=0.0, step=100.0, key=f"sv_{poz}", label_visibility="collapsed")
                cc[5].number_input("i", min_value=0.0, step=100.0, key=f"si_{poz}", label_visibility="collapsed")
                depoda = max(0, gelen - veren); yukte = max(0, veren - imalat)
                bad = imalat > veren + 1e-6 or veren > gelen + 1e-6
                kcol = "#fb7185" if bad else "#c7e8e4"
                cc[6].markdown(f'<div style="font-size:10px;padding-top:6px;color:{kcol};text-align:right;line-height:1.3">'
                               f'depo {depoda:,.0f}<br>yük {yukte:,.0f}</div>', unsafe_allow_html=True)
            else:
                # Yüklenici: sadece imalat girişi
                cc[3].markdown('<div style="font-size:10px;padding-top:9px;color:#3d556e;text-align:center">—</div>', unsafe_allow_html=True)
                cc[4].markdown('<div style="font-size:10px;padding-top:9px;color:#3d556e;text-align:center">—</div>', unsafe_allow_html=True)
                cc[5].number_input("i", min_value=0.0, step=100.0, key=f"si_{poz}", label_visibility="collapsed")
                pct = (imalat / r["miktar"] * 100) if r["miktar"] else 0
                cc[6].markdown(f'<div style="font-size:11px;padding-top:8px;color:#34d399;text-align:right">%{pct:.0f}</div>', unsafe_allow_html=True)
            if cc[7].button("💾", key=f"stsave_{poz}", help="Kaydet"):
                m = storage.load_stok(conn).set_index("poz")
                g = max(0.0, float(st.session_state.get(f"sg_{poz}", 0)))
                v = max(0.0, float(st.session_state.get(f"sv_{poz}", 0)))
                i = max(0.0, float(st.session_state.get(f"si_{poz}", 0)))
                if not is_isv:
                    g = 0.0; v = 0.0
                m.loc[poz, ["gelen", "veren", "imalat"]] = [g, v, i]
                storage.save_stok(conn, m.reset_index())
                st.toast(f"✅ Kaydedildi: {r['ad'][:30]}")
                st.rerun()
    else:
        rows = ""
        for _, r in sl.iterrows():
            is_isv = r["sorumluluk"] == "İşveren"
            scol = "#fbbf24" if is_isv else "#22d3ee"
            iw = max(0, min(100, r["imalat_pct"]))
            mcol = "#fb7185" if not r["mutabakat"] else "#c7e8e4"
            gelen_c = f'{r["gelen"]:,.0f}' if is_isv else "—"
            veren_c = f'{r["veren"]:,.0f}' if is_isv else "—"
            depo_yuk = f'{r["depoda_kalan"]:,.0f} / {r["yuklenicide"]:,.0f}' if is_isv else "—"
            rows += (f'<tr><td style="color:#5f7a99;font-size:10px">{r["poz"]}</td>'
                     f'<td class="mx-name" style="font-size:11px;max-width:230px">{r["ad"][:44]}</td>'
                     f'<td style="text-align:center;color:{scol};font-size:9.5px;font-weight:700">{"İşveren" if is_isv else "Yüklenici"}</td>'
                     f'<td style="text-align:right;color:#9fc3e0;font-size:10.5px">{r["miktar"]:,.0f} {r["birim"]}</td>'
                     f'<td style="text-align:right;color:#38bdf8;font-size:10.5px">{gelen_c}</td>'
                     f'<td style="text-align:right;color:#a78bfa;font-size:10.5px">{veren_c}</td>'
                     f'<td style="text-align:right;color:#22d3ee;font-size:10.5px">{r["imalat"]:,.0f}</td>'
                     f'<td style="text-align:center;color:{mcol};font-size:9.5px">{depo_yuk}</td>'
                     f'<td style="min-width:70px"><div style="position:relative;background:#0e2233;border-radius:5px;height:15px;overflow:hidden">'
                     f'<div style="position:absolute;left:0;top:0;height:100%;width:{iw:.0f}%;background:#34d399;border-radius:5px"></div>'
                     f'<span style="position:absolute;left:6px;top:0;line-height:15px;font-size:9px;font-weight:800;color:#e8f4ff">%{iw:.0f}</span></div></td></tr>')
        st.markdown(f'<table class="mx"><tr><th>POZ</th><th>MALZEME</th><th style="text-align:center">SORUMLU</th>'
                    f'<th style="text-align:right">SÖZLEŞME</th><th style="text-align:right">GELEN</th>'
                    f'<th style="text-align:right">VERİLEN</th><th style="text-align:right">İMALAT</th>'
                    f'<th style="text-align:center">DEPO/YÜK</th><th>İMALAT %</th></tr>{rows}</table>', unsafe_allow_html=True)

elif page == "Rapor & Yedek":
    st.markdown('<div class="panel-ttl">📊 Rapor İndir — Excel / PDF</div>', unsafe_allow_html=True)
    st.caption("Projenin güncel durumunu paylaşmak için profesyonel Excel veya PDF raporu indirin.")
    gag = core.group_agg(base)
    state = dict(df=base, k=core.kpis(base), disc=core.disc_agg(base, "ALL"), gag=gag,
        delayed=core.delayed_items(base), stock=st.session_state.stock, hse=st.session_state.hse,
        meta=meta, baseline=core.s_curve_baseline(core.kpis(base)["BAC"], meta["start"], meta["end"]),
        snaps=core.s_curve_from_snapshots(storage.load_snapshots(conn, "ALL")))
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    d1, d2 = st.columns(2)
    with d1:
        with st.spinner("Excel hazırlanıyor…"):
            xls = exports.build_excel(state)
        st.download_button("⬇️ Excel (.xlsx) indir", xls, file_name=f"ARAKONAK_GES_{ts}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch", type="primary")
        st.caption("İş Programı ilerlemesi, hakedişe esas imalat, stok durumu ve grup özetleri.")
    with d2:
        with st.spinner("PDF hazırlanıyor…"):
            pdf = exports.build_pdf(state)
        st.download_button("⬇️ PDF rapor indir", pdf, file_name=f"ARAKONAK_GES_{ts}.pdf",
            mime="application/pdf", width="stretch", type="primary")
        st.caption("Logolu yönetici raporu: KPI · grafikler · geciken işler")

    st.divider()
    st.markdown('<div class="panel-ttl">💾 Yedek & Geri Yükleme</div>', unsafe_allow_html=True)
    st.warning("💡 Verileriniz sunucuda geçici tutulur. **Düzenli olarak Tam Yedek dosyasını indirin** "
               "(ör. her hafta) — böylece bir sorun olursa geri yükleyebilirsiniz.")
    b1, b2 = st.columns(2)
    with b1:
        full = json.dumps(storage.export_all(conn), ensure_ascii=False, indent=1).encode("utf-8")
        st.download_button("⬇️ TAM YEDEK (.json) indir — tüm veriler", full,
                           file_name=f"arakonak_TAMYEDEK_{datetime.now():%Y%m%d_%H%M}.json",
                           mime="application/json", width="stretch", type="primary")
        st.caption("İş programı ilerlemesi · hakedişe esas imalat · stok durumu · ayarlar — tüm veriler tek dosyada.")
    with b2:
        csv = st.session_state.df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ Sadece iş kalemleri (CSV)", csv, file_name="arakonak_iskalemleri.csv",
                           mime="text/csv", width="stretch")

    if ADMIN:
        st.divider()
        st.markdown("**Geri yükleme**")
        upj = st.file_uploader("Tam yedek (.json) geri yükle", type=["json"])
        if upj is not None:
            try:
                storage.import_all(conn, json.loads(upj.getvalue().decode("utf-8")))
                for kk in ("df", "stock", "hse"):
                    st.session_state.pop(kk, None)
                for kk in [x for x in list(st.session_state.keys()) if str(x).startswith(("ep_", "er_", "ea_"))]:
                    st.session_state.pop(kk, None)
                st.success("Tam yedek geri yüklendi."); st.rerun()
            except Exception as ex:
                st.error(f"Okunamadı: {ex}")
        up = st.file_uploader("Sadece iş kalemleri CSV geri yükle", type=["csv"])
        if up is not None:
            try:
                new = pd.read_csv(up)
                if not {"id", "plan", "real"}.issubset(new.columns):
                    st.error("CSV'de gerekli sütunlar yok (id, plan, real).")
                else:
                    cur = st.session_state.df.set_index("id"); ni = new.set_index("id")
                    for c in ("plan", "real", "ac"):
                        if c in ni.columns:
                            cur.loc[ni.index, c] = ni[c].values
                    st.session_state.df = cur.reset_index()
                    for kk in [x for x in list(st.session_state.keys()) if str(x).startswith(("ep_", "er_", "ea_"))]:
                        st.session_state.pop(kk, None)
                    persist_progress()
                    st.success("Geri yüklendi."); st.rerun()
            except Exception as ex:
                st.error(f"Okunamadı: {ex}")

    st.divider()
    with st.expander("☁️ Google Sheets ile kalıcı senkron (opsiyonel kurulum)"):
        st.markdown(
            "Streamlit Cloud verisi geçici olduğundan, kalıcılık için bir **Google servis hesabı** bağlayabilirsiniz:\n\n"
            "1. Google Cloud'da bir **servis hesabı** oluşturup JSON anahtarını indirin.\n"
            "2. Bir Google Sheet açıp bu hesabın e-postasıyla **paylaşın** (Editör).\n"
            "3. Streamlit → **Manage app → Settings → Secrets** içine anahtarı `[gcp_service_account]` başlığıyla ve "
            "`sheet_id = \"...\"` satırını ekleyin.\n\n"
            "Bağlantı kurulduğunda uygulama her kayıtta Sheet'e yazar. Anahtar yoksa uygulama SQLite + yedekle sorunsuz çalışır.")
        connected = False
        try:
            connected = "gcp_service_account" in st.secrets
        except Exception:
            connected = False
        st.caption(("🟢 Google Sheets anahtarı bulundu." if connected
                    else "⚪ Henüz Google Sheets anahtarı eklenmemiş — yerel (SQLite + yedek) modda çalışıyor."))

elif page == "Ayarlar":
    if not ADMIN:
        st.info("Ayarları yalnızca admin değiştirebilir.")
    else:
        s1, s2 = st.columns(2)
        pname = s1.text_input("Proje adı", meta["name"])
        ploc = s2.text_input("Konum", meta["loc"])
        d1, d2 = st.columns(2)
        pstart = d1.date_input("Başlangıç tarihi", meta["start"].date())
        pend = d2.date_input("Bitiş tarihi (hedef)", meta["end"].date())
        if st.button("💾 Ayarları kaydet", type="primary"):
            storage.set_setting(conn, "proj_name", pname); storage.set_setting(conn, "proj_loc", ploc)
            storage.set_setting(conn, "start", pstart.strftime("%Y-%m-%d"))
            storage.set_setting(conn, "end", pend.strftime("%Y-%m-%d"))
            st.success("Kaydedildi."); st.rerun()
        st.divider()
        st.markdown("**🔐 Yeni parola hash'i üret** (Secrets'a eklemek için)")
        pw = st.text_input("Parola", type="password", key="pwgen")
        if pw:
            st.code(auth.hash_password(pw), language="text")

st.markdown("<div style='text-align:center;color:#9fb3b5;font-size:11px;margin-top:20px'>"
            "ARAKONAK GES · Kontrol Panosu · verileriniz yalnızca sizin dağıtımınızda tutulur</div>",
            unsafe_allow_html=True)
