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
PAGES = ["Komuta Paneli", "Arakonak 1-2 GES", "Stok & İmalat", "İş Programı", "Rapor & Yedek", "Ayarlar"]
ICON = {"Komuta Paneli": "▦", "Arakonak 1-2 GES": "🏗", "Stok & İmalat": "📦", "İş Programı": "📅",
        "Rapor & Yedek": "⭳", "Ayarlar": "⚙"}
with st.sidebar:
    _logo_b64 = LOGO_WHITE if theme == "dark" else LOGO_BLACK
    if _logo_b64:
        st.markdown(f'<div class="rail-logo"><img src="data:image/svg+xml;base64,{_logo_b64}"/></div>',
                    unsafe_allow_html=True)
    page = st.radio("Menü", [f"{ICON[p]}  {p}" for p in PAGES], label_visibility="collapsed")
    page = page.split("  ", 1)[1]

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
        <div class="kpi-label">KAZANILAN (EV)</div><div class="kpi-value" style="color:{TEAL}">{core.fmt_money(k['comp'])}</div>
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

    # Yönetici özeti + uyarılar
    st.markdown(f'<div style="background:linear-gradient(90deg,rgba(34,211,238,.10),rgba(139,92,246,.06));'
                f'border:1px solid {THEMES[theme]["border"]};border-radius:12px;padding:10px 15px;'
                f'font-size:12.5px;color:{THEMES[theme]["text"]};margin-bottom:10px">🧭 <b>Yönetici Özeti:</b> '
                f'{core.narrative(k, scope_label)}</div>', unsafe_allow_html=True)
    # Üst şerit: Toplam Bütçe · Kazanılan (EV) · Kalan İş (grafiklerin üstünde)
    st.markdown(
        f'<div style="display:flex;gap:10px;margin-bottom:14px;flex-wrap:wrap">'
        f'<div style="flex:1;min-width:200px;background:rgba(56,189,248,.08);border:1px solid #123a44;'
        f'border-radius:10px;padding:11px 16px"><span style="color:#38bdf8;font-size:10.5px;font-weight:700;letter-spacing:.5px">TOPLAM BÜTÇE</span>'
        f'<div style="color:#e6f4f4;font-size:20px;font-weight:800">{core.fmt_money(k["budget"])}</div></div>'
        f'<div style="flex:1;min-width:200px;background:rgba(34,211,238,.08);border:1px solid #123a44;'
        f'border-radius:10px;padding:11px 16px"><span style="color:#22d3ee;font-size:10.5px;font-weight:700;letter-spacing:.5px">KAZANILAN (EV)</span>'
        f'<div style="color:#e6f4f4;font-size:20px;font-weight:800">{core.fmt_money(k["comp"])}</div></div>'
        f'<div style="flex:1;min-width:200px;background:rgba(251,113,133,.08);border:1px solid #402028;'
        f'border-radius:10px;padding:11px 16px"><span style="color:#fb7185;font-size:10.5px;font-weight:700;letter-spacing:.5px">KALAN İŞ</span>'
        f'<div style="color:#e6f4f4;font-size:20px;font-weight:800">{core.fmt_money(k["kalan"])}</div></div>'
        f'</div>', unsafe_allow_html=True)

    hero = st.columns([1, 1.15], gap="medium")
    with hero[0]:
        with st.container(border=True):
            st.markdown('<div class="panel-ttl">Genel Fiziki İlerleme</div>', unsafe_allow_html=True)
            st.plotly_chart(charts.progress_donut(k["ilerleme"], k["planPct"]),
                            width="stretch", config=PLOT)
            st.markdown(f'<div style="text-align:center">'
                        f'<span class="nchip">PLANA GÖRE %{k["planPct"]:.0f}</span>'
                        f'<span class="nchip" style="color:{spi_col}">SPI {spi} {spi_arrow}</span></div>',
                        unsafe_allow_html=True)
    with hero[1]:
        with st.container(border=True):
            st.markdown('<div class="panel-ttl">GES-1 / GES-2 / ORTAK İlerleme</div>', unsafe_allow_html=True)
            _sched = storage.load_schedule(conn)
            _ges = core.ges_progress(_sched, pd.Timestamp.today().normalize())
            st.plotly_chart(charts.group_gauges(_ges), width="stretch", config=PLOT)
            st.caption("Sarı çizgi = plana göre olması gereken · Renkli dolgu = gerçekleşen (İş Programı'ndan).")

    with st.container(border=True):
        st.markdown('<div class="panel-ttl">Kümülatif S-Eğrisi</div>', unsafe_allow_html=True)
        gran = gran_buttons("dash_scurve")
        snaps_g = core.scurve_series_gran(storage.load_snapshots(conn, scope), gran)
        snaps_use = snaps_g if not snaps_g.empty else snaps
        st.plotly_chart(charts.s_curve(baseline, snaps_use, k["planPct"], k["ilerleme"],
                                       xstart=meta["start"], xend=meta["end"]),
                        width="stretch", config=PLOT)
        if baseline.empty:
            st.caption("💡 Plan çizgisi için aşağıdaki **Plan Programı**'na aylık Plan % girin. "
                       "Gerçek çizgi İş Kalemleri'ne veri girdikçe ilerler.")
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

    with st.container(border=True):
        st.markdown('<div class="panel-ttl">Disiplin Matrisi — Koşullu Biçimlendirme</div>', unsafe_allow_html=True)
        matrix_table(g)

elif page == "Arakonak 1-2 GES":
    kpi_ribbon()
    if ADMIN:
        cadd, cdel = st.columns(2)
        with cadd:
            with st.expander("➕ Yeni İş Kalemi Ekle", expanded=False):
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
        with cdel:
            with st.expander("🗑 İş Kalemi Sil", expanded=False):
                del_map = {f'{r["disc"]} — {r["name"][:50]}': r["id"] for _, r in scoped.iterrows()}
                del_sel = st.multiselect("Silinecek kalem(ler)", list(del_map.keys()))
                if st.button("Seçilenleri sil", disabled=not del_sel, width="stretch"):
                    delete_items([del_map[x] for x in del_sel])
                    st.toast(f"{len(del_sel)} kalem silindi."); st.rerun()
    else:
        st.info("Görüntüleyici modu: tablo salt-okunur.")

    f1, f2, f3 = st.columns([1, 2, 2])
    grp_view = f1.selectbox("Grup", ["(Tümü)"] + sorted(base["grp"].unique().tolist()), index=0)
    disc_view = f2.selectbox("Disiplin", ["(Tümü)"] + sorted(scoped["disc"].unique().tolist()), index=0)
    search = f3.text_input("🔎 Poz adında ara", "")
    view = base if grp_view == "(Tümü)" else base[base["grp"] == grp_view]
    if disc_view != "(Tümü)":
        view = view[view["disc"] == disc_view]
    if search.strip():
        view = view[view["name"].str.contains(search.strip(), case=False, na=False)]

    st.markdown(f'<div style="color:#7fb0b3;font-size:12px;margin:6px 0">Görüntülenen: '
                f'<b>{len(view)}</b> kalem · Toplam <b>{core.fmt_money(view["tutar"].sum())}</b></div>',
                unsafe_allow_html=True)

    edit_mode = False
    if ADMIN:
        edit_mode = st.toggle("✏️ Düzenleme modu", value=False,
                              help="Açıkken kalemler düzenlenebilir forma dönüşür; kapalıyken salt görünüm.")

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
        # widget değerlerini önceden session_state'e tohumla (form/value+key bayatlık sorununu önler)
        for _, r in sl.iterrows():
            st.session_state.setdefault(f"ep_{r['id']}", int(round(r["plan"])))
            st.session_state.setdefault(f"er_{r['id']}", int(round(r["real"])))
        with st.form("edit_items", border=False):
            h = st.columns([3.4, 1.1, 0.8, 1.1, 1.3, 1.3, 1.3])
            h[0].markdown("**Poz Adı**"); h[1].markdown("**Miktar**"); h[2].markdown("**Birim**")
            h[3].markdown("**Birim Fiyat**"); h[4].markdown("**Tutar**")
            h[5].markdown("**Plan %**"); h[6].markdown("**Gerçek %**")
            ids = []
            for _, r in sl.iterrows():
                ids.append(r["id"])
                c = st.columns([3.4, 1.1, 0.8, 1.1, 1.3, 1.3, 1.3])
                c[0].markdown(f'<div class="row-edit" style="font-size:11px;padding-top:8px;color:#dbeafe">'
                              f'{r["name"][:60]}</div>', unsafe_allow_html=True)
                c[1].markdown(f'<div style="font-size:11px;padding-top:8px;color:#9fc3e0;text-align:right">{r["qty"]:,.0f}</div>', unsafe_allow_html=True)
                c[2].markdown(f'<div style="font-size:11px;padding-top:8px;color:#7fb0b3">{r["unit"]}</div>', unsafe_allow_html=True)
                c[3].markdown(f'<div style="font-size:11px;padding-top:8px;color:#9fc3e0;text-align:right">${r["up"]:,.2f}</div>', unsafe_allow_html=True)
                c[4].markdown(f'<div style="font-size:11px;padding-top:8px;color:#c7e8e4;text-align:right">{core.fmt_money(r["tutar"])}</div>', unsafe_allow_html=True)
                c[5].number_input("p", 0, 100, key=f"ep_{r['id']}", label_visibility="collapsed")
                c[6].number_input("r", 0, 100, key=f"er_{r['id']}", label_visibility="collapsed")
            saved = st.form_submit_button("💾 Kaydet — grafiklere yansıt", type="primary", width="stretch")
        if saved:
            cur = st.session_state.df.set_index("id")
            n_upd = 0
            for rid in ids:
                old = cur.loc[rid]
                nm = str(old["name"])[:40]
                p = float(st.session_state.get(f"ep_{rid}", old["plan"]))
                rl = float(st.session_state.get(f"er_{rid}", old["real"]))
                p = max(0.0, min(100.0, p)); rl = max(0.0, min(100.0, rl))
                changed = False
                if abs(p - float(old["plan"])) > 1e-9:
                    storage.log_change(conn, user["username"], nm, "Plan %", f"{old['plan']:.0f}", f"{p:.0f}"); changed = True
                if abs(rl - float(old["real"])) > 1e-9:
                    storage.log_change(conn, user["username"], nm, "Gerçek %", f"{old['real']:.0f}", f"{rl:.0f}"); changed = True
                if changed:
                    st.session_state.df.loc[st.session_state.df["id"] == rid, ["plan", "real"]] = [p, rl]
                    n_upd += 1
            if n_upd:
                persist_progress()
                st.success(f"✅ {n_upd} kalem kaydedildi · grafikler ve S-Eğrisi güncellendi.")
                st.toast(f"{n_upd} kalem kaydedildi.")
            else:
                st.toast("Değişiklik yok.")
            st.rerun()
    else:
        items_table_html(view)

elif page == "Stok & İmalat":
    st.markdown('<div style="background:linear-gradient(90deg,rgba(251,191,36,.10),rgba(52,211,153,.05));'
                'border:1px solid #12324a;border-radius:12px;padding:12px 16px;font-size:12.5px;'
                'color:#cfe3f7;margin-bottom:14px">📦 <b>Stok & İmalat Durumu (Malzeme Mutabakatı):</b> '
                'Düzenleme modunu açıp her kaleme <b>Sahaya Gelen</b> ve <b>İmalata Giren</b> miktarını girin. '
                'Kalan stok, stok değeri, imalat %% ve <b>hakedişe esas tutar</b> anında hesaplanır ve grafiğe yansır. '
                '<i>Kural: Sahaya Gelen = İmalata Giren + Kalan Stok</i>.</div>', unsafe_allow_html=True)

    stok = storage.load_stok(conn)
    se = core.stok_enrich(stok)
    oz = core.stok_ozet(stok)

    # ── KPI ŞERİDİ ──
    tot = se["tutar"].sum()
    gelen_pct = se["gelen_pct"].mul(se["tutar"]).sum() / tot if tot else 0
    imalat_pct = se["imalat_pct"].mul(se["tutar"]).sum() / tot if tot else 0
    c = st.columns(5)
    c[0].metric("Sahaya Gelen Değer", core.fmt_money(oz["gelen_deger"]),
                delta=f"%{gelen_pct:.0f} tedarik", delta_color="off")
    c[1].metric("Hakedişe Esas (imalat)", core.fmt_money(oz["hakedise_esas"]),
                delta=f"%{imalat_pct:.0f} imalat", delta_color="off")
    c[2].metric("Kalan Stok Değeri", core.fmt_money(oz["stok_deger"]),
                help="Sahada bekleyen, henüz imal edilmemiş malzemenin bedeli")
    c[3].metric("Stok Devir Oranı", f"%{oz['devir']:.0f}",
                help="Gelen malzemenin imalata dönüşme oranı")
    c[4].metric("Mutabakatsız Kalem", oz["mutabakatsiz"], delta_color="inverse")

    if oz["mutabakatsiz"] > 0:
        st.markdown(f'<div style="background:rgba(251,113,133,.12);border:1px solid #fb7185;border-radius:10px;'
                    f'padding:9px 13px;font-size:12px;color:#fecdd3;margin:6px 0 10px">🔴 <b>Mutabakatsızlık:</b> '
                    f'{oz["mutabakatsiz"]} kalemde imalat, sahaya gelenden fazla. Malzeme kaydı kontrol edilmeli.</div>',
                    unsafe_allow_html=True)

    # ── GRAFİK ──
    with st.container(border=True):
        st.markdown('<div class="panel-ttl">Grup Bazında — Hakedişe Esas (imalat) + Kalan Stok Değeri</div>', unsafe_allow_html=True)
        st.plotly_chart(charts.stok_bar(core.stok_grup_agg(stok)), width="stretch", config=PLOT)

    # ── FİLTRE ──
    f1, f2, f3 = st.columns([1.4, 1.4, 1])
    grp_view = f1.selectbox("Grup", ["(Tümü)"] + sorted(se["grup"].unique().tolist()), key="stok_grp")
    ara = f2.text_input("Malzeme adında ara", key="stok_ara", placeholder="ör. panel, kablo...")
    only_stok = f3.checkbox("Sadece stoklu", value=False, key="stok_only")
    view = se if grp_view == "(Tümü)" else se[se["grup"] == grp_view]
    if ara:
        view = view[view["ad"].str.contains(ara, case=False, na=False)]
    if only_stok:
        view = view[view["kalan_stok"] > 0]

    st.caption(f"Görüntülenen: {len(view)} kalem · Kalan stok değeri {core.fmt_money(view['stok_deger'].sum())} · "
               f"Hakedişe esas {core.fmt_money(view['hakedise_esas'].sum())}".replace("$", "\\$"))

    edit_mode = st.toggle("✏️ Düzenleme modu — günlük stok/imalat girişi", value=False, key="stok_edit") if ADMIN else False

    # pagination
    PAGE = 40
    pages_n = max(1, (len(view) + PAGE - 1) // PAGE)
    if len(view) > PAGE:
        pg = st.number_input(f"Sayfa (her sayfada {PAGE} kalem · toplam {pages_n} sayfa)",
                             1, pages_n, 1, key="stok_page")
    else:
        pg = 1
    sl = view.iloc[(pg - 1) * PAGE: pg * PAGE]

    if edit_mode:
        for _, r in sl.iterrows():
            st.session_state.setdefault(f"sg_{r['poz']}", float(r["gelen"]))
            st.session_state.setdefault(f"si_{r['poz']}", float(r["imalat"]))
        with st.form("stok_edit_form", border=False):
            h = st.columns([3.2, 1.1, 0.8, 1.3, 1.3, 1.1, 1.2, 1.2])
            h[0].markdown("**Malzeme**"); h[1].markdown("**Sözleşme**"); h[2].markdown("**Birim**")
            h[3].markdown("**Sahaya Gelen**"); h[4].markdown("**İmalata Giren**"); h[5].markdown("**Kalan Stok**")
            h[6].markdown("**Stok $**"); h[7].markdown("**Hakediş $**")
            pozlar = []
            for _, r in sl.iterrows():
                pozlar.append(r["poz"])
                gelen = st.session_state.get(f"sg_{r['poz']}", r["gelen"])
                imalat = st.session_state.get(f"si_{r['poz']}", r["imalat"])
                kalan = max(0, gelen - imalat)
                mut_bad = imalat > gelen + 1e-6
                cc = st.columns([3.2, 1.1, 0.8, 1.3, 1.3, 1.1, 1.2, 1.2])
                cc[0].markdown(f'<div style="font-size:11px;padding-top:8px;color:#dbeafe">{r["ad"][:52]}</div>', unsafe_allow_html=True)
                cc[1].markdown(f'<div style="font-size:11px;padding-top:8px;color:#9fc3e0;text-align:right">{r["miktar"]:,.0f}</div>', unsafe_allow_html=True)
                cc[2].markdown(f'<div style="font-size:11px;padding-top:8px;color:#7fb0b3">{r["birim"]}</div>', unsafe_allow_html=True)
                cc[3].number_input("g", min_value=0.0, step=100.0, key=f"sg_{r['poz']}", label_visibility="collapsed")
                cc[4].number_input("i", min_value=0.0, step=100.0, key=f"si_{r['poz']}", label_visibility="collapsed")
                kcol = "#fb7185" if mut_bad else "#c7e8e4"
                cc[5].markdown(f'<div style="font-size:11px;padding-top:8px;color:{kcol};text-align:right">{kalan:,.0f}</div>', unsafe_allow_html=True)
                cc[6].markdown(f'<div style="font-size:11px;padding-top:8px;color:#fbbf24;text-align:right">{core.fmt_money(kalan*r["bf"])}</div>', unsafe_allow_html=True)
                cc[7].markdown(f'<div style="font-size:11px;padding-top:8px;color:#34d399;text-align:right">{core.fmt_money(imalat*r["bf"])}</div>', unsafe_allow_html=True)
            saved = st.form_submit_button("💾 Kaydet — grafiğe ve yüzdelere yansıt", type="primary", width="stretch")
        if saved:
            m = storage.load_stok(conn).set_index("poz")
            n = 0
            for poz in pozlar:
                g = float(st.session_state.get(f"sg_{poz}", 0)); i = float(st.session_state.get(f"si_{poz}", 0))
                if abs(g - float(m.loc[poz, "gelen"])) > 1e-6 or abs(i - float(m.loc[poz, "imalat"])) > 1e-6:
                    m.loc[poz, ["gelen", "imalat"]] = [max(0, g), max(0, i)]; n += 1
            if n:
                storage.save_stok(conn, m.reset_index())
                st.success(f"✅ {n} kalem güncellendi · grafik ve yüzdeler yenilendi.")
                st.rerun()
            else:
                st.toast("Değişiklik yok.")
    else:
        rows = ""
        for _, r in sl.iterrows():
            mcol = "#fb7185" if not r["mutabakat"] else "#c7e8e4"
            iw = max(0, min(100, r["imalat_pct"])); gw = max(0, min(100, r["gelen_pct"]))
            rows += (f'<tr><td style="color:#5f7a99;font-size:10px">{r["poz"]}</td>'
                     f'<td class="mx-name" style="font-size:11px;max-width:260px">{r["ad"][:48]}</td>'
                     f'<td style="text-align:right;color:#9fc3e0;font-size:10.5px">{r["miktar"]:,.0f} {r["birim"]}</td>'
                     f'<td style="text-align:right;color:#38bdf8;font-size:10.5px">{r["gelen"]:,.0f}</td>'
                     f'<td style="text-align:right;color:#22d3ee;font-size:10.5px">{r["imalat"]:,.0f}</td>'
                     f'<td style="text-align:right;color:{mcol};font-size:10.5px">{r["kalan_stok"]:,.0f}</td>'
                     f'<td style="min-width:90px"><div style="position:relative;background:#0e2233;border-radius:5px;height:15px;overflow:hidden">'
                     f'<div style="position:absolute;left:0;top:0;height:100%;width:{iw:.0f}%;background:#34d399;border-radius:5px"></div>'
                     f'<span style="position:absolute;left:6px;top:0;line-height:15px;font-size:9px;font-weight:800;color:#e8f4ff">%{iw:.0f}</span></div></td>'
                     f'<td style="text-align:right;color:#fbbf24;font-size:10.5px">{core.fmt_money(r["stok_deger"])}</td>'
                     f'<td style="text-align:right;color:#34d399;font-size:10.5px">{core.fmt_money(r["hakedise_esas"])}</td></tr>')
        st.markdown(f'<table class="mx"><tr><th>POZ</th><th>MALZEME</th><th style="text-align:right">SÖZLEŞME</th>'
                    f'<th style="text-align:right">GELEN</th><th style="text-align:right">İMALAT</th>'
                    f'<th style="text-align:right">KALAN STOK</th><th>İMALAT %</th>'
                    f'<th style="text-align:right">STOK $</th><th style="text-align:right">HAKEDİŞE ESAS</th></tr>{rows}</table>',
                    unsafe_allow_html=True)


elif page == "İş Programı":
    st.markdown('<div style="background:linear-gradient(90deg,rgba(34,211,238,.10),rgba(139,92,246,.06));'
                'border:1px solid #12324a;border-radius:12px;padding:12px 16px;font-size:12.5px;'
                'color:#cfe3f7;margin-bottom:14px">📅 <b>İş Programı (Primavera P6) — ZAMAN boyutu:</b> 64 faaliyetin '
                'planlanan tarihleri, Gantt ve <b>gecikme analizi</b>. Buraya faaliyet bazında ilerleme %\'si girip '
                '<b>"bugün ne kadar olmalıydı"</b> ile kıyaslarsınız. '
                '<i>(Para/hakediş takibi ayrı: Arakonak 1-2 GES sayfasında.)</i></div>', unsafe_allow_html=True)

    sched = storage.load_schedule(conn)
    today = pd.Timestamp.today().normalize()

    # ── Sürekli Excel yükleme (ilerleme güncelleme) ──
    if ADMIN:
        with st.expander("📥 İlerleme Excel'i Yükle (her yüklemede program güncellenir)"):
            st.caption("Faaliyet adı + ilerleme % içeren Excel yükleyin. Sistem isim benzerliğiyle eşleştirip "
                       "gerçekleşmeyi günceller, gecikme ve tahmini bitişi yeniden hesaplar.")
            up = st.file_uploader("Excel (.xlsx)", type=["xlsx"], key="sched_upload")
            if up is not None:
                try:
                    xl = pd.read_excel(up, sheet_name=0)
                    new_sched, n = core.match_progress_excel(sched, xl)
                    if n > 0:
                        storage.save_schedule(conn, new_sched)
                        st.success(f"✅ {n} faaliyet güncellendi. Grafikler yenilendi.")
                        st.rerun()
                    else:
                        st.warning("Eşleşen faaliyet bulunamadı. Excel'de faaliyet adı ve % sütunu olduğundan emin olun.")
                except Exception as e:
                    st.error(f"Excel okunamadı: {str(e)[:80]}")

    summ = core.sched_summary(sched, today)
    stt = core.sched_status(sched, today)
    gecikme = stt[stt["durum"] == "Gecikme"]
    tamam = stt[stt["durum"] == "Tamamlandı"]
    fin = core.sched_finish_estimate(sched, meta["start"], today)
    planned_finish = pd.Timestamp(meta["end"])

    cS = st.columns(5)
    cS[0].metric("Programa Göre Olması Gereken", f"%{summ['plan']:.1f}")
    cS[1].metric("Gerçekleşen", f"%{summ['real']:.1f}",
                 delta=f"{summ['sapma']:+.1f} puan", delta_color="normal" if summ['sapma'] >= 0 else "inverse")
    cS[2].metric("Geciken Faaliyet", len(gecikme), delta_color="inverse")
    cS[3].metric("Planlanan Bitiş", planned_finish.strftime("%d.%m.%Y"))
    if fin["tahmini"] is not None:
        gecikme_gun = (fin["tahmini"] - planned_finish).days
        cS[4].metric("Tahmini Bitiş", fin["tahmini"].strftime("%d.%m.%Y"),
                     delta=f"{gecikme_gun:+d} gün", delta_color="inverse" if gecikme_gun > 0 else "normal")
    else:
        cS[4].metric("Tahmini Bitiş", "—", help="İlerleme girildikçe hesaplanır")

    if fin["tahmini"] is not None and (fin["tahmini"] - planned_finish).days > 7:
        st.markdown(f'<div style="background:rgba(251,113,133,.12);border:1px solid #fb7185;border-radius:10px;'
                    f'padding:9px 13px;font-size:12px;color:#fecdd3;margin-bottom:10px">🔴 <b>Gecikme riski:</b> '
                    f'mevcut hızla proje <b>{fin["tahmini"].strftime("%d.%m.%Y")}</b>\'de biter — '
                    f'planlanan {planned_finish.strftime("%d.%m.%Y")}\'den <b>{(fin["tahmini"]-planned_finish).days} gün</b> sonra.</div>',
                    unsafe_allow_html=True)
    elif summ["sapma"] >= 0 and summ["real"] > 0:
        st.markdown(f'<div style="background:rgba(52,211,153,.12);border:1px solid #34d399;border-radius:10px;'
                    f'padding:9px 13px;font-size:12px;color:#bbf7d0;margin-bottom:10px">🟢 <b>Program önünde/uyumlu.</b></div>',
                    unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="panel-ttl">Gantt — Faaliyet Zaman Çizelgesi (kırmızı çizgi = bugün)</div>', unsafe_allow_html=True)
        st.plotly_chart(charts.gantt(sched, today), width="stretch", config=PLOT)

    if len(gecikme) > 0:
        st.markdown('<div class="panel-ttl">⚠️ Geciken Faaliyetler — öncelik verilmeli</div>', unsafe_allow_html=True)
        gg = gecikme.sort_values("sapma").copy()
        rows = ""
        for _, r in gg.iterrows():
            rows += (f'<tr><td class="mx-name">{r["ad"]}</td>'
                     f'<td style="color:#9fc3e0;font-size:11px">{r["grup"]}</td>'
                     f'<td style="color:#7fb0b3;font-size:11px">{r["bitis"].strftime("%d.%m.%Y")}</td>'
                     f'<td style="text-align:center;color:#a78bfa">%{r["plan_pct"]:.0f}</td>'
                     f'<td style="text-align:center;color:#22d3ee">%{r["gercek"]:.0f}</td>'
                     f'<td style="text-align:center"><span class="mx-pill" style="background:#fb718522;color:#fb7185">{r["sapma"]:.0f} puan</span></td></tr>')
        st.markdown(f'<table class="mx"><tr><th>FAALİYET</th><th>GRUP</th><th>PLANLANAN BİTİŞ</th>'
                    f'<th style="text-align:center">OLMASI GEREKEN</th><th style="text-align:center">GERÇEK</th>'
                    f'<th style="text-align:center">SAPMA</th></tr>{rows}</table>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="panel-ttl">Program S-Eğrisi — Planlanan (tarihlerden) vs Gerçek</div>', unsafe_allow_html=True)
        base_c = core.sched_curve(sched, meta["start"], meta["end"])
        base_c = base_c.rename(columns={"planPct": "planPct"})
        real_c = core.sched_real_curve(sched)
        st.plotly_chart(charts.s_curve(base_c, real_c, summ["plan"], summ["real"],
                                       xstart=meta["start"], xend=meta["end"]),
                        width="stretch", config=PLOT)
        st.caption("Mor kesikli = iş programı tarihlerinden otomatik planlanan ilerleme · Yeşil = girdiğiniz gerçek tamamlanma.")

    if ADMIN:
        st.markdown('<div class="panel-ttl">Faaliyet Tamamlanma Girişi</div>', unsafe_allow_html=True)
        st.caption("Her faaliyetin gerçek tamamlanma %'sini girin. Gantt, gecikme listesi ve S-eğrisi anında güncellenir.")
        ed = sched[["id", "ad", "grup", "baslangic", "bitis", "gercek"]].copy()
        ed_show = st.data_editor(ed, width="stretch", hide_index=True, key="sched_ed",
                                 disabled=["id", "ad", "grup", "baslangic", "bitis"],
                                 column_config={
                                     "ad": st.column_config.TextColumn("Faaliyet"),
                                     "grup": st.column_config.TextColumn("Grup"),
                                     "baslangic": st.column_config.DateColumn("Başlangıç"),
                                     "bitis": st.column_config.DateColumn("Bitiş"),
                                     "gercek": st.column_config.NumberColumn("Gerçek %", min_value=0, max_value=100, step=5)})
        if not ed_show["gercek"].equals(ed["gercek"]):
            merged = sched.copy()
            merged["gercek"] = ed_show["gercek"].values
            storage.save_schedule(conn, merged)
            st.toast("İş programı güncellendi."); st.rerun()

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
        st.caption("7 sayfa: Özet · İş Kalemleri · Disiplin · Grup · Geciken İşler · Stok · İSG")
    with d2:
        with st.spinner("PDF hazırlanıyor…"):
            pdf = exports.build_pdf(state)
        st.download_button("⬇️ PDF rapor indir", pdf, file_name=f"ARAKONAK_GES_{ts}.pdf",
            mime="application/pdf", width="stretch", type="primary")
        st.caption("Logolu yönetici raporu: KPI · grafikler · geciken işler")

    st.divider()
    st.markdown('<div class="panel-ttl">💾 Yedek & Geri Yükleme</div>', unsafe_allow_html=True)
    st.warning("Streamlit Cloud deposu geçici olabilir. **Kalıcı güvence için düzenli Tam Yedek (JSON) indirin** "
               "veya aşağıdan Google Sheets kalıcı senkronunu kurun.")
    b1, b2 = st.columns(2)
    with b1:
        full = json.dumps(storage.export_all(conn), ensure_ascii=False, indent=1).encode("utf-8")
        st.download_button("⬇️ TAM YEDEK (.json) indir — tüm veriler", full,
                           file_name=f"arakonak_TAMYEDEK_{datetime.now():%Y%m%d_%H%M}.json",
                           mime="application/json", width="stretch", type="primary")
        st.caption("İş kalemleri, stok, İSG, günlük kayıtlar, baseline, risk/NCR/VO/hakediş, kayıt defteri — hepsi.")
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
