"""ARAKONAK GES İş Programı — Primavera P6 (Renevo) çıktısından.
64 faaliyet · 10 Haz 2026 → 24 Kas 2026. Grup, başlangıç, bitiş tarihleri."""

SCHEDULE = [
    # id, ad, grup, başlangıç, bitiş
    ("SAT100", "OG Kablo", "Satınalma (REN)", "2026-06-10", "2026-08-23"),
    ("SAT101", "AG Kablo", "Satınalma (REN)", "2026-06-10", "2026-08-23"),
    ("SAT102", "Topraklama", "Satınalma (REN)", "2026-06-10", "2026-07-06"),
    ("SAT107", "DCBox", "Satınalma (REN)", "2026-07-01", "2026-08-09"),
    ("SAT103", "DC Kablo", "Satınalma (REN)", "2026-07-15", "2026-08-13"),
    ("SAT108", "FO Kablo ve Sarf Malzemeler", "Satınalma (REN)", "2026-07-20", "2026-08-08"),
    ("SAT109", "CCTV", "Satınalma (REN)", "2026-08-09", "2026-09-07"),
    ("SAT111", "SCADA", "Satınalma (REN)", "2026-08-24", "2026-10-07"),
    ("SAT104", "AG Pano", "Satınalma (REN)", "2026-08-27", "2026-10-10"),
    ("SAT106", "Jeneratör", "Satınalma (REN)", "2026-08-27", "2026-10-10"),
    ("SAT110", "İç İhtiyaç Panosu", "Satınalma (REN)", "2026-08-27", "2026-10-10"),
    ("SAT105", "Kablo Başlıkları", "Satınalma (REN)", "2026-09-06", "2026-10-01"),
    ("SAT115", "Konstrüksiyon", "Satınalma (NAS)", "2026-06-30", "2026-08-30"),
    ("SAT112", "Panel", "Satınalma (NAS)", "2026-08-01", "2026-10-30"),
    ("SAT116", "Trafo", "Satınalma (NAS)", "2026-10-03", "2026-10-10"),
    ("SAT117", "OG Hücre", "Satınalma (NAS)", "2026-10-03", "2026-10-10"),
    ("INS100", "Grid Topraklaması", "İnşaat ARK-1", "2026-07-07", "2026-07-26"),
    ("INS101", "Delgi", "İnşaat ARK-1", "2026-07-09", "2026-08-02"),
    ("INS102", "Ayak Betonlama", "İnşaat ARK-1", "2026-07-12", "2026-08-07"),
    ("INS106", "Konstrüksiyon Montajı", "İnşaat ARK-1", "2026-08-04", "2026-09-08"),
    ("INS107", "Temel İmalatları", "İnşaat ARK-1", "2026-08-12", "2026-09-01"),
    ("INS110", "Tel Çit Montajı", "İnşaat ARK-1", "2026-09-04", "2026-09-27"),
    ("INS111", "Drenaj İmalatları", "İnşaat ARK-1", "2026-09-08", "2026-10-22"),
    ("INS112", "Panel Montajı", "İnşaat ARK-1", "2026-09-08", "2026-10-23"),
    ("INS113", "Yol İmalatları", "İnşaat ARK-1", "2026-09-13", "2026-10-27"),
    ("INS104", "Grid Topraklaması", "İnşaat ARK-2", "2026-07-27", "2026-08-20"),
    ("INS103", "Ayak Betonlama", "İnşaat ARK-2", "2026-07-27", "2026-08-25"),
    ("INS105", "Delgi", "İnşaat ARK-2", "2026-07-29", "2026-08-22"),
    ("INS108", "Konstrüksiyon Montajı", "İnşaat ARK-2", "2026-08-21", "2026-09-29"),
    ("INS109", "Temel İmalatları", "İnşaat ARK-2", "2026-08-27", "2026-09-15"),
    ("INS114", "Panel Montajı", "İnşaat ARK-2", "2026-09-20", "2026-11-08"),
    ("INS115", "Yol İmalatları", "İnşaat ARK-2", "2026-10-03", "2026-11-16"),
    ("INS116", "Drenaj İmalatları", "İnşaat ARK-2", "2026-10-03", "2026-11-11"),
    ("INS117", "Tel Çit Montajı", "İnşaat ARK-2", "2026-10-04", "2026-10-08"),
    ("ELK101", "OG Kablo Kazıları", "Elektrik ARK-1", "2026-08-24", "2026-09-02"),
    ("ELK102", "OG Kablo Serimi", "Elektrik ARK-1", "2026-08-29", "2026-09-12"),
    ("ELK110", "OG Kanal Kapatma", "Elektrik ARK-1", "2026-09-11", "2026-09-15"),
    ("ELK118", "Trafo Kurulumu", "Elektrik ARK-1", "2026-10-11", "2026-10-20"),
    ("ELK119", "Hücre Montajı", "Elektrik ARK-1", "2026-10-11", "2026-10-20"),
    ("ELK100", "AG-DC Kablo Kanal Kazıları", "Elektrik ARK-1", "2026-08-24", "2026-09-02"),
    ("ELK105", "AG-DC Borulama ve Kablo Serimi", "Elektrik ARK-1", "2026-09-03", "2026-09-12"),
    ("ELK107", "CCTV Kanal Kazıları", "Elektrik ARK-1", "2026-09-09", "2026-09-23"),
    ("ELK108", "AG Kanal Kapatımı", "Elektrik ARK-1", "2026-09-10", "2026-09-13"),
    ("ELK111", "Inverter Kurulumu", "Elektrik ARK-1", "2026-09-11", "2026-10-06"),
    ("ELK112", "CCTV Kablo Serimi", "Elektrik ARK-1", "2026-09-17", "2026-10-01"),
    ("ELK116", "Scada Donanım Kurulumu", "Elektrik ARK-1", "2026-10-08", "2026-10-17"),
    ("ELK121", "Solar Kablo Montajı", "Elektrik ARK-1", "2026-10-25", "2026-11-03"),
    ("ELK127", "Topraklama", "Elektrik ARK-1", "2026-11-04", "2026-11-13"),
    ("ELK104", "OG Kablo Kazıları", "Elektrik ARK-2", "2026-08-31", "2026-09-09"),
    ("ELK109", "OG Kablo Serimi", "Elektrik ARK-2", "2026-09-10", "2026-10-09"),
    ("ELK117", "OG Kanal Kapatma", "Elektrik ARK-2", "2026-10-10", "2026-10-29"),
    ("ELK123", "Trafo Kurulumu", "Elektrik ARK-2", "2026-10-21", "2026-10-30"),
    ("ELK124", "Hücre Montajı", "Elektrik ARK-2", "2026-10-21", "2026-10-30"),
    ("ELK103", "AG-DC Kablo Kanal Kazıları", "Elektrik ARK-2", "2026-08-29", "2026-09-07"),
    ("ELK106", "AG-DC Kablo Serimi", "Elektrik ARK-2", "2026-09-08", "2026-10-07"),
    ("ELK113", "CCTV Kanal Kazıları", "Elektrik ARK-2", "2026-09-29", "2026-10-23"),
    ("ELK115", "AG Kanal Kapatımı", "Elektrik ARK-2", "2026-10-03", "2026-11-01"),
    ("ELK114", "Inverter Kurulumu", "Elektrik ARK-2", "2026-10-03", "2026-10-27"),
    ("ELK120", "Scada Donanım Kurulumu", "Elektrik ARK-2", "2026-10-18", "2026-10-27"),
    ("ELK125", "CCTV Kablo Serimi", "Elektrik ARK-2", "2026-10-24", "2026-11-07"),
    ("ELK122", "Solar Kablo Montajı", "Elektrik ARK-2", "2026-10-25", "2026-11-03"),
    ("ELK126", "Topraklama", "Elektrik ARK-2", "2026-10-30", "2026-11-08"),
    ("TST100", "Devreye Alma Öncesi Testler", "Test & Devreye Alma", "2026-10-31", "2026-11-14"),
    ("TST101", "Devreye Alma Sonrası Testler", "Test & Devreye Alma", "2026-11-15", "2026-11-24"),
]


def schedule_df():
    import pandas as pd
    d = pd.DataFrame(SCHEDULE, columns=["id", "ad", "grup", "baslangic", "bitis"])
    d["baslangic"] = pd.to_datetime(d["baslangic"])
    d["bitis"] = pd.to_datetime(d["bitis"])
    d["sure_gun"] = (d["bitis"] - d["baslangic"]).dt.days + 1
    d["gercek"] = 0.0  # elle girilecek tamamlanma %
    return d
