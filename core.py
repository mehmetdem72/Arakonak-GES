"""ARAKONAK GES — Çekirdek hesap motoru.

Bu modül Streamlit'ten BAĞIMSIZDIR (import etmez), böylece ayrı test edilebilir.
İçerik: satır zenginleştirme, EVM (Kazanılmış Değer) metrikleri, disiplin/grup
kırılımları, geciken iş tespiti ve S-eğrisi (baseline + snapshot) hesapları.
"""
from __future__ import annotations

import math
import pandas as pd

from seed_data import SEED_ROWS

GROUPS = ["GES-1 EPC", "GES-2 EPC", "ORTAK EPC"]
GROUP_SHORT = {"GES-1 EPC": "GES-1", "GES-2 EPC": "GES-2", "ORTAK EPC": "ORTAK"}
SCOPE_MAP = {"Tümü": "ALL", "GES-1": "GES-1 EPC", "GES-2": "GES-2 EPC", "ORTAK": "ORTAK EPC"}

COLS = ["id", "grp", "disc", "name", "unit", "qty", "up", "plan", "real"]


# ────────────────────────────── VERİ ──────────────────────────────
def seed_df() -> pd.DataFrame:
    """Ana ilerleme tablosu — İŞ PROGRAMI (işveren yaklaşık maliyeti, GES-1/GES-2/ORTAK)."""
    import data_isprogram
    df = pd.DataFrame(data_isprogram.progress_rows())[COLS].copy()
    for c in ("qty", "up", "plan", "real"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    df["ac"] = 0.0
    return df


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Her satır için türetilmiş sütunları hesaplar."""
    df = df.copy()
    if "ac" not in df.columns:
        df["ac"] = 0.0
    df["tutar"] = df["qty"] * df["up"]              # BAC (poz bütçesi)
    df["planW"] = df["tutar"] * df["plan"] / 100.0  # PV — Planlanan Değer
    df["realW"] = df["tutar"] * df["real"] / 100.0  # EV — Kazanılmış Değer
    df["comp"] = df["realW"]
    df["kalan"] = df["tutar"] - df["comp"]
    df["sapma"] = df["real"] - df["plan"]           # ilerleme sapması (puan)

    def durum(r):
        if r["real"] >= 100: return "TAMAMLANDI"
        if r["real"] <= 0:   return "BAŞLAMADI"
        if r["real"] < r["plan"] - 1e-9: return "GERİDE"
        return "DEVAM"

    df["durum"] = df.apply(durum, axis=1)
    return df


def scope_df(df: pd.DataFrame, scope: str) -> pd.DataFrame:
    return df if scope == "ALL" else df[df["grp"] == scope]


# ────────────────────────────── EVM ──────────────────────────────
def kpis(df: pd.DataFrame) -> dict:
    """Snapshot EVM metrikleri. Maliyet metrikleri yalnızca AC girilmişse üretilir."""
    bac   = float(df["tutar"].sum())
    ev    = float(df["realW"].sum())
    pv    = float(df["planW"].sum())
    ac    = float(df.get("ac", pd.Series(dtype=float)).sum())

    ilerleme = (ev / bac * 100) if bac else 0.0
    planPct  = (pv / bac * 100) if bac else 0.0
    sv  = ev - pv
    spi = (ev / pv) if pv else None

    has_cost = ac > 0
    cv   = (ev - ac) if has_cost else None
    cpi  = (ev / ac) if has_cost else None
    eac  = (bac / cpi) if (has_cost and cpi) else None
    etc  = (eac - ac) if (eac is not None) else None
    vac  = (bac - eac) if (eac is not None) else None
    tcpi = ((bac - ev) / (bac - ac)) if (has_cost and (bac - ac) != 0) else None

    return {
        "budget": bac, "comp": ev, "kalan": bac - ev,
        "ilerleme": ilerleme, "planPct": planPct,
        "PV": pv, "EV": ev, "AC": ac, "BAC": bac,
        "SV": sv, "SPI": spi, "spi": spi,           # 'spi' geriye dönük uyum
        "CV": cv, "CPI": cpi, "EAC": eac, "ETC": etc, "VAC": vac, "TCPI": tcpi,
        "has_cost": has_cost,
    }


def status_counts(df: pd.DataFrame):
    vc = df["durum"].value_counts().to_dict()
    return [(s, int(vc.get(s, 0))) for s in ["TAMAMLANDI", "DEVAM", "GERİDE", "BAŞLAMADI"]]


def disc_agg(df_all: pd.DataFrame, scope: str) -> pd.DataFrame:
    scoped = scope_df(df_all, scope)
    g = scoped.groupby("disc").agg(
        budget=("tutar", "sum"), comp=("comp", "sum"),
        planW=("planW", "sum"), realW=("realW", "sum"), ac=("ac", "sum"),
    ).reset_index()
    g = g[g["budget"] > 0].copy()
    g["planPct"] = g["planW"] / g["budget"] * 100
    g["realPct"] = g["realW"] / g["budget"] * 100
    g["compPct"] = g["comp"] / g["budget"] * 100
    g["sapma"]   = g["realPct"] - g["planPct"]

    bg = df_all.groupby(["disc", "grp"]).agg(b=("tutar", "sum"), c=("comp", "sum")).reset_index()
    breakdown = {}
    for disc in g["disc"]:
        parts, sub = [], bg[bg["disc"] == disc]
        for grp in df_all["grp"].dropna().unique():
            row = sub[sub["grp"] == grp]
            if not row.empty and row["b"].iloc[0] > 0:
                sh = GROUP_SHORT.get(grp, str(grp)[:10])
                parts.append(f"{sh}: %{row['c'].iloc[0]/row['b'].iloc[0]*100:.0f}")
        breakdown[disc] = "   •   ".join(parts)
    g["breakdown"] = g["disc"].map(breakdown)
    return g.sort_values("budget", ascending=False)


def group_agg(df_all: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for grp in df_all["grp"].dropna().unique():
        sub = df_all[df_all["grp"] == grp]
        b = float(sub["tutar"].sum())
        if b <= 0:
            continue
        short = GROUP_SHORT.get(grp, str(grp)[:14])
        rows.append({
            "grp": grp, "short": short, "budget": b,
            "planPct": sub["planW"].sum() / b * 100,
            "realPct": sub["realW"].sum() / b * 100,
            "comp": float(sub["comp"].sum()), "kalan": b - float(sub["comp"].sum()),
        })
    out = pd.DataFrame(rows)
    return out.sort_values("budget", ascending=False) if not out.empty else out


def delayed_items(df: pd.DataFrame, top: int = 15) -> pd.DataFrame:
    """Geride kalan kalemleri, bütçeye göre ağırlıklı 'risk' skoruyla sıralar."""
    d = df[df["durum"] == "GERİDE"].copy()
    if d.empty:
        return d
    d["gecikme"] = (d["plan"] - d["real"]).clip(lower=0)          # puan
    d["riskUSD"] = d["tutar"] * d["gecikme"] / 100.0              # $ cinsinden etki
    return d.sort_values("riskUSD", ascending=False).head(top)


# ─────────────────────── S-EĞRİSİ (baseline + snapshot) ───────────────────────
def s_curve_baseline(bac: float, start, end, n: int = 24):
    """Proje başlangıç–bitişi arasında standart 'S' (kümülatif) baseline üretir.

    NOT: Bu MODELLENMİŞ bir baseline'dır (poz-poz zaman planı verisi olmadığından).
    Gerçek plan eğrisi için 'anlık görüntü' (snapshot) mekanizması kullanılır.
    """
    if not start or not end or end <= start:
        return pd.DataFrame(columns=["date", "planUSD", "planPct"])
    total_days = (end - start).days or 1
    xs = [start + pd.Timedelta(days=round(total_days * i / (n - 1))) for i in range(n)]
    out = []
    for dt in xs:
        t = ((dt - start).days) / total_days
        # yumuşak S: smootherstep
        s = 0 if t <= 0 else (1 if t >= 1 else t * t * t * (t * (t * 6 - 15) + 10))
        out.append({"date": pd.Timestamp(dt), "planUSD": bac * s, "planPct": s * 100})
    return pd.DataFrame(out)


def s_curve_from_snapshots(snaps: pd.DataFrame) -> pd.DataFrame:
    """Kaydedilmiş anlık görüntülerden gerçek PV/EV eğrisini kurar.

    snaps sütunları: ts (tarih), pv_pct, ev_pct, ac_usd, bac
    """
    if snaps is None or snaps.empty:
        return pd.DataFrame(columns=["date", "pvPct", "evPct", "acPct"])
    s = snaps.copy()
    s["date"] = pd.to_datetime(s["ts"]).dt.normalize()
    s = s.sort_values("date").groupby("date", as_index=False).last()
    s["pvPct"] = s["pv_pct"]
    s["evPct"] = s["ev_pct"]
    s["acPct"] = (s["ac_usd"] / s["bac"] * 100).where(s["bac"] > 0, 0)
    return s[["date", "pvPct", "evPct", "acPct"]]


# ────────────────────────────── BİÇİM ──────────────────────────────
def fmt_money(v) -> str:
    v = round(v or 0)
    if abs(v) >= 1e6: return f"${v/1e6:.2f}M"
    if abs(v) >= 1e3: return f"${v/1e3:.0f}K"
    return f"${v:.0f}"


def fmt_full(v) -> str:
    return f"${(v or 0):,.0f}".replace(",", ".")


def per_scope_kpis(base: pd.DataFrame) -> dict:
    """Her kapsam (ALL/GES-1/GES-2/ORTAK) için günlük kayıt metrikleri."""
    out = {}
    for label, scope in SCOPE_MAP.items():
        s = scope_df(base, scope)
        b = float(s["tutar"].sum())
        out[scope] = {
            "pv": (float(s["planW"].sum()) / b * 100) if b else 0.0,
            "ev": (float(s["realW"].sum()) / b * 100) if b else 0.0,
            "ac": float(s.get("ac", pd.Series(dtype=float)).sum()),
            "bac": b,
        }
    return out


def narrative(k: dict, scope_label: str = "Proje") -> str:
    """Otomatik yönetici özeti cümlesi."""
    ev, pl = k["ilerleme"], k["planPct"]
    diff = ev - pl
    yon = "planında" if abs(diff) < 0.5 else (f"{abs(diff):.0f} puan önde" if diff > 0 else f"{abs(diff):.0f} puan geride")
    spi_txt = "—" if k["SPI"] is None else f"{k['SPI']:.2f}"
    s = (f"{scope_label} <b>%{ev:.1f}</b> ilerlemede; plana göre <b>{yon}</b> (SPI {spi_txt}). "
         f"Kalan iş <b>{fmt_money(k['kalan'])}</b>.")
    return s


def alerts(df: pd.DataFrame, k: dict) -> list:
    """Eşik uyarıları — (seviye, mesaj)."""
    out = []
    if k["SPI"] is not None and k["SPI"] < 0.9:
        out.append(("risk", f"Zaman performansı düşük: SPI {k['SPI']:.2f} (<0.90) — proje planın gerisinde."))
    if k["has_cost"] and k["CPI"] is not None and k["CPI"] < 0.9:
        out.append(("risk", f"Maliyet performansı düşük: CPI {k['CPI']:.2f} (<0.90) — bütçe aşımı riski."))
    d = df.copy()
    d["planW"] = d["tutar"] * d["plan"] / 100
    d["realW"] = d["tutar"] * d["real"] / 100
    geride = d[(d["real"] < d["plan"] - 10)]
    if len(geride) > 0:
        tut = fmt_money(float((geride["tutar"]).sum()))
        out.append(("izle", f"{len(geride)} iş kalemi planının 10+ puan gerisinde (toplam {tut})."))
    if k["has_cost"] and k["EAC"] and k["EAC"] > k["BAC"] * 1.05:
        out.append(("risk", f"Öngörülen maliyet bütçeyi aşıyor: EAC {fmt_money(k['EAC'])} > BAC {fmt_money(k['BAC'])}."))
    if not out:
        out.append(("iyi", "Kritik eşik ihlali yok. Proje kontrol altında."))
    return out


def spi_cpi_series(snaps: pd.DataFrame) -> pd.DataFrame:
    """Günlük snapshot'lardan SPI ve CPI zaman serisi."""
    if snaps is None or snaps.empty:
        return pd.DataFrame(columns=["date", "SPI", "CPI"])
    s = snaps.copy()
    s["date"] = pd.to_datetime(s["ts"]).dt.normalize()
    s = s.sort_values("ts").groupby("date").last().reset_index()
    s["SPI"] = (s["ev_pct"] / s["pv_pct"]).where(s["pv_pct"] > 0)
    ev_usd = s["ev_pct"] / 100 * s["bac"]
    s["CPI"] = (ev_usd / s["ac_usd"]).where(s["ac_usd"] > 0)
    return s[["date", "SPI", "CPI"]]


def cashflow_series(baseline_df: pd.DataFrame, snaps: pd.DataFrame) -> pd.DataFrame:
    """Aylık planlanan (baseline'dan) vs kazanılan değer (EV = gerçek% × bütçe).
    Fiili maliyet girilmediğinden 'gerçekleşen' = tamamlanan işin bütçe değeridir."""
    if baseline_df is None or baseline_df.empty:
        return pd.DataFrame(columns=["month", "plan", "actual"])
    b = baseline_df.copy()
    b["month"] = b["date"].dt.strftime("%Y-%m")
    b = b.groupby("month", sort=True).last().reset_index()
    b["plan"] = b["planUSD"].diff().fillna(b["planUSD"]).clip(lower=0)
    out = b[["month", "plan"]].copy()
    out["actual"] = 0.0
    if snaps is not None and not snaps.empty:
        s = snaps.copy()
        s["month"] = pd.to_datetime(s["ts"]).dt.strftime("%Y-%m")
        s = s.sort_values("ts").groupby("month").last().reset_index()
        s["ev_usd"] = s["ev_pct"] / 100 * s["bac"]          # kazanılan değer ($)
        s["actual"] = s["ev_usd"].diff().fillna(s["ev_usd"]).clip(lower=0)
        out = out.merge(s[["month", "actual"]], on="month", how="left", suffixes=("", "_a"))
        out["actual"] = out["actual_a"].fillna(0.0) if "actual_a" in out else 0.0
        out = out[["month", "plan", "actual"]]
    return out


def month_rows(start, end) -> list:
    """Proje başlangıç–bitiş arası aylık satır iskeleti (manuel plan programı için)."""
    if not start or not end or end <= start:
        start = pd.Timestamp.today().normalize().replace(day=1)
        end = start + pd.Timedelta(days=330)
    months = pd.period_range(pd.Timestamp(start), pd.Timestamp(end), freq="M")
    return [{"Ay": str(m), "Plan %": None, "Gerçek %": None} for m in months]


def manual_curve(planline_df: pd.DataFrame, bac: float):
    """Elle girilen aylık Plan/Gerçek %'den S-eğrisi baseline + snapshot üretir.

    Dönüş: (baseline_df[date,planUSD,planPct], snaps_df[date,pvPct,evPct,acPct])
    Girilmemiş (boş) hücreler atlanır; hiç veri yoksa boş döner (model'e düşülür).
    """
    empty_b = pd.DataFrame(columns=["date", "planUSD", "planPct"])
    empty_s = pd.DataFrame(columns=["date", "pvPct", "evPct", "acPct"])
    if planline_df is None or planline_df.empty or "Ay" not in planline_df.columns:
        return empty_b, empty_s
    d = planline_df.copy()
    d["date"] = pd.to_datetime(d["Ay"].astype(str) + "-01", errors="coerce")
    d = d.dropna(subset=["date"]).sort_values("date")
    nan_series = pd.Series([float("nan")] * len(d), index=d.index)
    pl = pd.to_numeric(d["Plan %"], errors="coerce") if "Plan %" in d.columns else nan_series
    rl = pd.to_numeric(d["Gerçek %"], errors="coerce") if "Gerçek %" in d.columns else nan_series
    base = d[pl.notna()]
    baseline = pd.DataFrame({"date": base["date"], "planPct": pl[pl.notna()].clip(0, 100)})
    baseline["planUSD"] = baseline["planPct"] / 100 * bac
    mask = pl.notna() | rl.notna()
    snaps = pd.DataFrame({
        "date": d["date"][mask],
        "pvPct": pl[mask].ffill().fillna(0).clip(0, 100),
        "evPct": rl[mask].ffill().fillna(0).clip(0, 100),
        "acPct": 0.0,
    })
    if baseline.empty and snaps.empty:
        return empty_b, empty_s
    return baseline[["date", "planUSD", "planPct"]], snaps


def resample_snaps(snaps: pd.DataFrame, gran: str = "Günlük") -> pd.DataFrame:
    """Ham snapshot'ları granülariteye göre yeniden örnekler (Günlük/Haftalık/Aylık).
    Her dönemin SON değeri alınır (kümülatif % için doğru)."""
    if snaps is None or snaps.empty:
        return snaps
    s = snaps.copy()
    s["date"] = pd.to_datetime(s["ts"]).dt.normalize()
    s = s.sort_values("date")
    rule = {"Günlük": "D", "Haftalık": "W", "Aylık": "ME"}.get(gran, "D")
    if rule == "D":
        g = s.groupby("date", as_index=False).last()
    else:
        g = s.set_index("date").resample(rule).last().dropna(how="all").reset_index()
    return g


def spi_cpi_series_gran(snaps: pd.DataFrame, gran: str = "Günlük") -> pd.DataFrame:
    """SPI/CPI zaman serisi — granülariteye göre (Günlük/Haftalık/Aylık)."""
    g = resample_snaps(snaps, gran)
    if g is None or g.empty:
        return pd.DataFrame(columns=["date", "SPI", "CPI"])
    g = g.dropna(subset=["ev_pct"])
    g["SPI"] = (g["ev_pct"] / g["pv_pct"]).where(g["pv_pct"] > 0)
    ev_usd = g["ev_pct"] / 100 * g["bac"]
    g["CPI"] = (ev_usd / g["ac_usd"]).where(g["ac_usd"] > 0)
    return g[["date", "SPI", "CPI"]]


def scurve_series_gran(snaps: pd.DataFrame, gran: str = "Günlük") -> pd.DataFrame:
    """S-eğrisi gerçek/plan serisi — granülariteye göre."""
    g = resample_snaps(snaps, gran)
    if g is None or g.empty:
        return pd.DataFrame(columns=["date", "pvPct", "evPct", "acPct"])
    g = g.dropna(subset=["ev_pct"])
    g["pvPct"] = g["pv_pct"]; g["evPct"] = g["ev_pct"]
    g["acPct"] = (g["ac_usd"] / g["bac"] * 100).where(g["bac"] > 0, 0)
    return g[["date", "pvPct", "evPct", "acPct"]]


# ══════════════ İŞ PROGRAMI (SCHEDULE) ══════════════
def sched_planned_pct(act_df, asof=None):
    """Bir faaliyetin verilen tarihteki PLANLANAN tamamlanma %'si (tarihlerden, lineer)."""
    if asof is None:
        asof = pd.Timestamp.today().normalize()
    asof = pd.Timestamp(asof)
    s = act_df["baslangic"]; f = act_df["bitis"]
    dur = (f - s).dt.days.clip(lower=1)
    pct = ((asof - s).dt.days / dur * 100).clip(0, 100)
    return pct


def sched_summary(act_df, asof=None):
    """İş programı özeti: ağırlıklı planlanan % ve gerçek % (süre-ağırlıklı)."""
    if act_df is None or act_df.empty:
        return {"plan": 0.0, "real": 0.0, "sapma": 0.0}
    if asof is None:
        asof = pd.Timestamp.today().normalize()
    d = act_df.copy()
    d["plan_pct"] = sched_planned_pct(d, asof)
    w = d["sure_gun"].clip(lower=1)
    plan = float((d["plan_pct"] * w).sum() / w.sum())
    real = float((pd.to_numeric(d["gercek"], errors="coerce").fillna(0) * w).sum() / w.sum())
    return {"plan": plan, "real": real, "sapma": real - plan, "asof": asof}


def sched_status(act_df, asof=None):
    """Her faaliyetin durumunu etiketler: Tamamlandı / Devam / Gecikme / Başlamadı."""
    if asof is None:
        asof = pd.Timestamp.today().normalize()
    asof = pd.Timestamp(asof)
    d = act_df.copy()
    d["plan_pct"] = sched_planned_pct(d, asof)
    d["gercek"] = pd.to_numeric(d["gercek"], errors="coerce").fillna(0)
    def _st(r):
        if r["gercek"] >= 100: return "Tamamlandı"
        if asof < r["baslangic"]: return "Başlamadı"
        if r["gercek"] + 1e-6 < r["plan_pct"] - 10: return "Gecikme"
        if r["gercek"] > 0: return "Devam"
        if asof >= r["baslangic"]: return "Gecikme"
        return "Başlamadı"
    d["durum"] = d.apply(_st, axis=1)
    d["sapma"] = d["gercek"] - d["plan_pct"]
    return d


def sched_curve(act_df, start, end, n=40):
    """İş programından PLANLANAN kümülatif S-eğrisi (tarihlerden, süre-ağırlıklı)."""
    if act_df is None or act_df.empty or not start or not end:
        return pd.DataFrame(columns=["date", "planPct"])
    dates = pd.date_range(pd.Timestamp(start), pd.Timestamp(end), periods=n)
    w = act_df["sure_gun"].clip(lower=1)
    rows = []
    for dt in dates:
        pp = sched_planned_pct(act_df, dt)
        rows.append({"date": dt, "planPct": float((pp * w).sum() / w.sum())})
    return pd.DataFrame(rows)


def sched_real_curve(act_df):
    """Faaliyet bitiş tarihlerine göre GERÇEK kümülatif % (girilen tamamlanmalardan)."""
    if act_df is None or act_df.empty:
        return pd.DataFrame(columns=["date", "evPct", "pvPct", "acPct"])
    d = act_df.copy()
    d["gercek"] = pd.to_numeric(d["gercek"], errors="coerce").fillna(0)
    w = d["sure_gun"].clip(lower=1)
    total = w.sum()
    # her faaliyetin katkısı bitiş tarihinde tamamlanmış sayılır (gerçek% oranında)
    d = d.sort_values("bitis")
    d["katki"] = d["gercek"] / 100 * w / total * 100
    d["evPct"] = d["katki"].cumsum()
    d["pvPct"] = 0.0; d["acPct"] = 0.0
    return d[["bitis", "evPct", "pvPct", "acPct"]].rename(columns={"bitis": "date"})


# ══════════════ İŞVEREN ↔ YÜKLENİCİ KARŞILAŞTIRMA ══════════════
# Yüklenici grubu / İşveren disiplini → ortak karşılaştırma grubu


def sched_finish_estimate(sched_df, start, today=None):
    """Gerçek ilerleme hızına göre TAHMİNİ bitiş tarihi.
    Hız = bugüne kadarki gerçek% / geçen gün. Kalan işi bu hızla bitirme tarihi."""
    if today is None:
        today = pd.Timestamp.today().normalize()
    today = pd.Timestamp(today); start = pd.Timestamp(start)
    summ = sched_summary(sched_df, today)
    actual = summ["real"]
    elapsed = max(1, (today - start).days)
    if actual <= 0.5:
        return {"tahmini": None, "gercek": actual, "hiz": 0.0}
    rate = actual / elapsed                    # %/gün
    remaining = max(0.0, 100.0 - actual)
    days_left = remaining / rate if rate > 0 else None
    est = today + pd.Timedelta(days=days_left) if days_left is not None else None
    return {"tahmini": est, "gercek": actual, "hiz": rate, "gun_kaldi": days_left}


def match_progress_excel(sched_df, upload_df):
    """Yüklenen Excel'deki faaliyet adı + ilerleme %'yi mevcut programa eşler (isim benzerliği).
    Dönüş: güncellenmiş sched_df + eşleşen satır sayısı."""
    import difflib
    up = upload_df.copy()
    up.columns = [str(c).strip().lower() for c in up.columns]
    # ad ve yüzde sütunlarını tahmin et
    name_col = next((c for c in up.columns if any(k in c for k in ["faaliyet", "iş", "is", "activity", "ad", "kalem", "poz"])), up.columns[0])
    pct_col = next((c for c in up.columns if any(k in c for k in ["%", "yüzde", "yuzde", "gerçek", "gercek", "ilerleme", "tamam", "percent", "progress"])), None)
    if pct_col is None:
        num_cols = [c for c in up.columns if up[c].dtype.kind in "if"]
        pct_col = num_cols[-1] if num_cols else None
    if pct_col is None:
        return sched_df, 0
    sched = sched_df.copy()
    names = sched["ad"].astype(str).str.lower().tolist()
    matched = 0
    for _, r in up.iterrows():
        nm = str(r.get(name_col, "")).strip().lower()
        if not nm:
            continue
        try:
            val = float(r.get(pct_col))
        except Exception:
            continue
        if val <= 1.0:
            val *= 100  # oran → yüzde
        val = max(0.0, min(100.0, val))
        hit = difflib.get_close_matches(nm, names, n=1, cutoff=0.6)
        if hit:
            idx = names.index(hit[0])
            sched.iloc[idx, sched.columns.get_loc("gercek")] = val
            matched += 1
    return sched, matched


# ══════════════ GES-1 / GES-2 / ORTAK İLERLEME (iş programından) ══════════════
def ges_progress(df, asof=None):
    """İş Programı kalemlerini GES-1 / GES-2 / ORTAK olarak gruplar (bütçe-ağırlıklı).
    df: ana ilerleme tablosu (enrich edilmiş) — grp sütunu GES-1/GES-2/ORTAK."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["grp", "short", "realPct", "planPct", "budget"])
    d = df.copy()
    if "tutar" not in d.columns:
        d["tutar"] = d["qty"] * d["up"]
    for c in ("plan", "real"):
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    rows = []
    for z in ["GES-1", "GES-2", "ORTAK"]:
        sub = d[d["grp"] == z]
        if sub.empty:
            continue
        b = float(sub["tutar"].sum())
        if b <= 0:
            continue
        rows.append({
            "grp": z, "short": z,
            "realPct": float((sub["tutar"] * sub["real"]).sum() / b / 100 * 100) if b else 0,
            "planPct": float((sub["tutar"] * sub["plan"]).sum() / b / 100 * 100) if b else 0,
            "budget": b,
        })
    return pd.DataFrame(rows)


# ══════════════ STOK & İMALAT (MALZEME MUTABAKATI) ══════════════
def stok_enrich(df):
    """Stok tablosunu zenginleştirir: kalan stok, imalat %, stok değeri, hakedişe esas."""
    d = df.copy()
    for c in ("miktar", "bf", "tutar", "gelen", "imalat"):
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0.0)
    d["kalan_stok"] = (d["gelen"] - d["imalat"]).clip(lower=0)
    d["imalat_pct"] = (d["imalat"] / d["miktar"].replace(0, pd.NA) * 100).fillna(0).clip(0, 100)
    d["gelen_pct"] = (d["gelen"] / d["miktar"].replace(0, pd.NA) * 100).fillna(0).clip(0, 100)
    d["stok_deger"] = d["kalan_stok"] * d["bf"]              # sahada bekleyen malzeme değeri
    d["hakedise_esas"] = d["imalat"] * d["bf"]               # yapılan imalatın parasal karşılığı
    # mutabakat: imalat gelenden fazla olamaz
    d["mutabakat"] = d["imalat"] <= d["gelen"] + 1e-6
    return d


def stok_ozet(df):
    """Stok sayfası üst kartları için özet."""
    d = stok_enrich(df)
    return {
        "gelen_deger": float((d["gelen"] * d["bf"]).sum()),
        "hakedise_esas": float(d["hakedise_esas"].sum()),
        "stok_deger": float(d["stok_deger"].sum()),
        "devir": float(d["imalat"].sum() / d["gelen"].sum() * 100) if d["gelen"].sum() > 0 else 0.0,
        "mutabakatsiz": int((~d["mutabakat"]).sum()),
    }


def stok_grup_agg(df):
    """Grup bazında gelen / imalat / kalan stok değeri (grafik için)."""
    d = stok_enrich(df)
    d["gelen_deger"] = d["gelen"] * d["bf"]
    g = d.groupby("grup").agg(
        gelen=("gelen_deger", "sum"),
        imalat=("hakedise_esas", "sum"),
        stok=("stok_deger", "sum"),
    ).reset_index().sort_values("gelen", ascending=False)
    return g


# ══════════════ HAKEDİŞE ESAS İMALAT (yüklenici) ══════════════
def hakedis_enrich(df):
    """Yüklenici imalat: kalan miktar, imalat %, hakedişe esas tutar."""
    d = df.copy()
    for c in ("miktar", "bf", "tutar", "imalat"):
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0.0)
    d["kalan"] = (d["miktar"] - d["imalat"]).clip(lower=0)
    d["imalat_pct"] = (d["imalat"] / d["miktar"].replace(0, pd.NA) * 100).fillna(0).clip(0, 100)
    d["hakedise_esas"] = d["imalat"] * d["bf"]          # yapılan imalatın parasal karşılığı
    d["kalan_tutar"] = d["kalan"] * d["bf"]
    return d


def hakedis_ozet(df):
    d = hakedis_enrich(df)
    bac = float(d["tutar"].sum())
    he = float(d["hakedise_esas"].sum())
    return {
        "bac": bac, "hakedise_esas": he,
        "kalan_tutar": float(d["kalan_tutar"].sum()),
        "imalat_pct": (he / bac * 100) if bac else 0.0,
    }


def hakedis_grup_agg(df):
    d = hakedis_enrich(df)
    g = d.groupby("grup").agg(
        bac=("tutar", "sum"), imalat=("hakedise_esas", "sum"), kalan=("kalan_tutar", "sum"),
    ).reset_index().sort_values("bac", ascending=False)
    g["pct"] = (g["imalat"] / g["bac"] * 100).fillna(0)
    return g
