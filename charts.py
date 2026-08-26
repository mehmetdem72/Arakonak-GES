"""ARAKONAK GES — Plotly grafik kütüphanesi (kurumsal tema)."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

import core

# ── Tema paleti (set_theme ile değişir) ──
C_OK = "#22d3ee"; C_OK_D = "#0891b2"; C_REM = "#fb7185"
C_PLAN = "#8b5cf6"; C_PLAN_D = "#7c3aed"; C_AMB = "#fbbf24"; C_PUR = "#a78bfa"
C_INK = "#e5edf7"; C_INK2 = "#a7bad4"; C_GRID = "rgba(255,255,255,.07)"
C_HOVER = "#0f1a2e"; C_TRACK = "rgba(255,255,255,.08)"; C_TICK = "#8fa3bd"
FONT = "Inter, 'Segoe UI', system-ui, sans-serif"


def set_theme(name="dark"):
    """Tüm grafik renklerini 'dark' veya 'light' temaya göre ayarlar."""
    global C_OK, C_OK_D, C_REM, C_PLAN, C_PLAN_D, C_AMB, C_PUR
    global C_INK, C_INK2, C_GRID, C_HOVER, C_TRACK, C_TICK
    if name == "light":
        C_OK, C_OK_D = "#0d9488", "#0a7268"
        C_REM, C_PLAN, C_PLAN_D = "#e11d48", "#6366f1", "#4f46e5"
        C_AMB, C_PUR = "#d97706", "#0891b2"
        C_INK, C_INK2 = "#0f2b3a", "#37525c"
        C_GRID = "rgba(15,43,58,.08)"; C_HOVER = "#0f2b3a"
        C_TRACK = "#eef2f6"; C_TICK = "#7a86b8"
    else:
        C_OK, C_OK_D = "#22d3ee", "#0891b2"
        C_REM, C_PLAN, C_PLAN_D = "#fb7185", "#a78bfa", "#7c3aed"
        C_AMB, C_PUR = "#fbbf24", "#67e8f9"
        C_INK, C_INK2 = "#dbeafe", "#9fc3e0"
        C_GRID = "rgba(34,211,238,.08)"; C_HOVER = "#0a1422"
        C_TRACK = "rgba(34,211,238,.10)"; C_TICK = "#5f7a99"


def _style(fig, height, corner=6, legend=True):
    fig.update_layout(
        height=height, margin=dict(l=8, r=14, t=30, b=8),
        font=dict(family=FONT, size=12, color=C_INK2),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=legend,
        legend=dict(orientation="h", y=1.17, x=0, xanchor="left",
                    font=dict(size=11, color=C_INK2), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor=C_HOVER, font=dict(family=FONT, color="white", size=12),
                        bordercolor="rgba(255,255,255,.15)"), bargap=0.30)
    try: fig.update_layout(barcornerradius=corner)
    except Exception: pass
    fig.update_xaxes(showgrid=True, gridcolor=C_GRID, zeroline=False,
                     tickfont=dict(color=C_TICK, size=10), title=None)
    fig.update_yaxes(showgrid=False, zeroline=False,
                     tickfont=dict(color=C_INK2, size=10.5), title=None)
    return fig


def s_curve(baseline: pd.DataFrame, snaps: pd.DataFrame, today_pv, today_ev, today_ac=None,
            xstart=None, xend=None):
    """Tamamen elle girilen plan + gerçek eğrisi + bugünkü nokta.
    xstart/xend verilirse x ekseni proje zaman çizgisine yayılır (tek gün varken saat gösterimini önler)."""
    fig = go.Figure()
    has_base = baseline is not None and not baseline.empty
    if has_base:
        fig.add_scatter(x=baseline["date"], y=baseline["planPct"], name="Plan (elle girilen)",
                        mode="lines+markers", line=dict(color=C_PLAN, width=2.5, dash="dot"),
                        marker=dict(size=5), hovertemplate="%{x|%d.%m.%Y}<br>Plan %{y:.1f}%<extra></extra>")
    if snaps is not None and not snaps.empty:
        fig.add_scatter(x=snaps["date"], y=snaps["evPct"], name="Gerçek",
                        mode="lines+markers", line=dict(color=C_OK, width=3),
                        marker=dict(size=7), hovertemplate="%{x|%d.%m.%Y}<br>Gerçek %{y:.1f}%<extra></extra>")
        if not has_base:
            fig.add_scatter(x=snaps["date"], y=snaps["pvPct"], name="Plan (girilen)",
                            mode="lines+markers", line=dict(color=C_PLAN_D, width=1.5, dash="dash"),
                            marker=dict(size=5), hovertemplate="%{x|%d.%m.%Y}<br>Plan %{y:.1f}%<extra></extra>")
        if (snaps["acPct"] > 0).any():
            fig.add_scatter(x=snaps["date"], y=snaps["acPct"], name="Maliyet (AC)",
                            mode="lines+markers", line=dict(color=C_AMB, width=1.5),
                            marker=dict(size=5), hovertemplate="%{x|%d.%m.%Y}<br>AC %{y:.1f}%<extra></extra>")
    # bugünkü canlı nokta (güne sabit)
    now = pd.Timestamp.today().normalize()
    fig.add_scatter(x=[now], y=[today_ev], name="Bugün", mode="markers",
                    marker=dict(size=13, color=C_OK, line=dict(color="white", width=2)),
                    hovertemplate="Bugün<br>Gerçek %{y:.1f}%<extra></extra>")
    _style(fig, 360)
    fig.update_yaxes(range=[0, 105], ticksuffix="%", showgrid=True, gridcolor=C_GRID)
    # x eksenini proje aralığına yay + TÜRKÇE ay etiketleri
    if xstart is not None and xend is not None:
        try:
            TR_AY = ["Oca", "Şub", "Mar", "Nis", "May", "Haz",
                     "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
            months = pd.date_range(pd.Timestamp(xstart).replace(day=1),
                                   pd.Timestamp(xend), freq="MS")
            fig.update_xaxes(range=[pd.Timestamp(xstart), pd.Timestamp(xend)],
                             tickmode="array",
                             tickvals=list(months),
                             ticktext=[f"{TR_AY[m.month-1]} {m.year}" for m in months])
        except Exception:
            pass
    return fig


def progress_donut(pct, plan_pct=None):
    """Açık kurumsal halka gösterge — Genel İlerleme."""
    pct = max(0, min(100, pct))
    fig = go.Figure(go.Pie(
        values=[pct, 100 - pct], hole=0.72, sort=False, direction="clockwise", rotation=0,
        marker=dict(colors=[C_OK, C_TRACK], line=dict(color="rgba(0,0,0,0)", width=0)),
        textinfo="none", hoverinfo="skip"))
    ann = [dict(text=f"<b>%{pct:.0f}</b>", x=0.5, y=0.52, font=dict(size=30, color=C_OK, family=FONT), showarrow=False),
           dict(text="EV / BAC", x=0.5, y=0.36, font=dict(size=11, color="#8aa", family=FONT), showarrow=False)]
    if plan_pct is not None:
        ann.append(dict(text=f"plan %{plan_pct:.0f}", x=0.5, y=0.20,
                        font=dict(size=10, color=C_PLAN, family=FONT), showarrow=False))
    fig.update_layout(annotations=ann, height=210, margin=dict(l=6, r=6, t=6, b=6),
                      showlegend=False, paper_bgcolor="rgba(0,0,0,0)", font=dict(family=FONT))
    return fig


def group_gauges(gag: pd.DataFrame, top: int = 8):
    """Grup performansı — çok gruba uygun yatay çubuk (gerçek% + plan çizgisi)."""
    if gag is None or gag.empty:
        return _style(go.Figure(), 220)
    d = gag.sort_values("budget", ascending=True).tail(top)
    fig = go.Figure()
    labels = d["short"].tolist()
    real = d["realPct"].round(0).tolist()
    plan = d["planPct"].round(0).tolist()
    # arka plan (100%)
    fig.add_trace(go.Bar(y=labels, x=[100] * len(d), orientation="h",
                         marker=dict(color=C_TRACK), hoverinfo="skip", showlegend=False, width=0.62))
    # gerçekleşen
    colors = [C_OK if r >= p else C_AMB for r, p in zip(real, plan)]
    fig.add_trace(go.Bar(y=labels, x=real, orientation="h",
                         marker=dict(color=colors),
                         text=[f"%{v:.0f}" for v in real], textposition="inside",
                         insidetextanchor="start", textfont=dict(size=11, color="#04222b", family=FONT),
                         hovertemplate="%{y}<br>Gerçek %{x:.0f}<extra></extra>", showlegend=False, width=0.62))
    # plan çizgisi (marker)
    fig.add_trace(go.Scatter(y=labels, x=plan, mode="markers",
                             marker=dict(symbol="line-ns", size=16, color="#fbbf24",
                                         line=dict(width=2, color="#fbbf24")),
                             hovertemplate="%{y}<br>Plan %{x:.0f}<extra></extra>", showlegend=False))
    _style(fig, max(220, len(d) * 30))
    fig.update_layout(barmode="overlay", bargap=0.35, margin=dict(l=8, r=10, t=8, b=8))
    fig.update_xaxes(range=[0, 100], showgrid=False, showticklabels=False)
    fig.update_yaxes(tickfont=dict(size=10.5, color=C_INK))
    return fig


def gantt(sched_df, today=None):
    """İş programı Gantt: faaliyet çubukları + tamamlanma + bugün çizgisi."""
    import pandas as pd
    fig = go.Figure()
    if sched_df is None or sched_df.empty:
        _style(fig, 600); return fig
    if today is None:
        today = pd.Timestamp.today().normalize()
    d = sched_df.copy().sort_values(["grup", "baslangic"], ascending=[True, False]).reset_index(drop=True)
    d["gercek"] = pd.to_numeric(d["gercek"], errors="coerce").fillna(0)
    grup_renk = {}
    palette = ["#22d3ee", "#34d399", "#a78bfa", "#fbbf24", "#38bdf8", "#2dd4bf", "#f472b6"]
    for i, g in enumerate(d["grup"].unique()):
        grup_renk[g] = palette[i % len(palette)]
    ylabels = []
    for i, r in d.iterrows():
        y = i
        ylabels.append(f"{r['ad'][:34]}")
        dur_ms = (r["bitis"] - r["baslangic"]).days + 1
        col = grup_renk[r["grup"]]
        # plan çubuğu (arka, soluk)
        fig.add_trace(go.Bar(y=[y], x=[dur_ms], base=[r["baslangic"]], orientation="h",
            marker=dict(color=col, opacity=0.28, line=dict(color=col, width=1)),
            hovertemplate=f"{r['ad']}<br>{r['grup']}<br>%{{base|%d.%m.%Y}} → {r['bitis'].strftime('%d.%m.%Y')}<br>Plan süre {dur_ms}g<extra></extra>",
            showlegend=False, width=0.62))
        # gerçek (ilerleme) çubuğu
        if r["gercek"] > 0:
            prog_ms = dur_ms * r["gercek"] / 100
            fig.add_trace(go.Bar(y=[y], x=[prog_ms], base=[r["baslangic"]], orientation="h",
                marker=dict(color=col, line=dict(color="#04222b", width=0.5)),
                hovertemplate=f"{r['ad']}<br>Gerçek %{r['gercek']:.0f}<extra></extra>",
                showlegend=False, width=0.42))
    # bugün çizgisi
    fig.add_vline(x=today, line=dict(color="#fb7185", width=2, dash="dash"))
    fig.update_yaxes(tickmode="array", tickvals=list(range(len(d))), ticktext=ylabels,
                     autorange="reversed", tickfont=dict(size=10, color=C_INK))
    TR_AY = ["Oca","Şub","Mar","Nis","May","Haz","Tem","Ağu","Eyl","Eki","Kas","Ara"]
    months = pd.date_range(d["baslangic"].min().replace(day=1), d["bitis"].max(), freq="MS")
    fig.update_xaxes(type="date", tickmode="array", tickvals=list(months),
                     ticktext=[f"{TR_AY[m.month-1]} {m.year}" for m in months],
                     gridcolor=C_GRID, showgrid=True)
    _style(fig, max(600, len(d) * 22))
    fig.update_layout(barmode="overlay", bargap=0.15, margin=dict(l=8, r=8, t=8, b=8))
    return fig


def compare_bar(cmp_df):
    """İşveren vs Yüklenici — grup bazlı yatay karşılaştırma çubuğu."""
    import pandas as pd
    fig = go.Figure()
    if cmp_df is None or cmp_df.empty:
        _style(fig, 400); return fig
    d = cmp_df.sort_values("isveren", ascending=True)
    fig.add_trace(go.Bar(y=d["grup"], x=d["isveren"], name="İşveren Keşfi", orientation="h",
                         marker=dict(color=C_PLAN, opacity=0.85),
                         hovertemplate="%{y}<br>İşveren: $%{x:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(y=d["grup"], x=d["yuklenici"], name="Yüklenici Hakedişi", orientation="h",
                         marker=dict(color=C_OK, opacity=0.85),
                         hovertemplate="%{y}<br>Yüklenici: $%{x:,.0f}<extra></extra>"))
    _style(fig, max(420, len(d) * 34))
    fig.update_xaxes(tickprefix="$", tickformat=".2s", showgrid=True, gridcolor=C_GRID)
    fig.update_layout(barmode="group", bargap=0.25, legend=dict(orientation="h", y=1.08))
    return fig
