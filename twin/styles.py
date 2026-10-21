"""CSS for the SCADA-style Streamlit UI."""

from __future__ import annotations


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
html, body, .stApp { font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif; }
.stApp {
  background:
    radial-gradient(1100px 520px at 8% -8%, #162b4d 0%, rgba(22,43,77,0) 60%),
    radial-gradient(900px 480px at 100% 0%, #211a3d 0%, rgba(33,26,61,0) 55%),
    #0b1220;
  color: #e5e7eb;
}
header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1560px; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f172a, #0b1220); border-right: 1px solid #1d2b45; }
[data-testid="stSidebar"] * { color: #cbd5e1; }
[data-testid="stSidebar"] [data-testid="stExpander"] { border: 1px solid #22324d; border-radius: 12px; background: rgba(17,26,46,.55); margin-bottom: .45rem; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary { font-weight: 700; letter-spacing: .03em; }
[data-testid="stWidgetLabel"] p { color: #cbd5e1 !important; font-weight: 500; }
.stApp h1, .stApp h2, .stApp h3 { color: #f1f5f9; letter-spacing: -0.01em; }
[data-testid="stCaptionContainer"] { color: #8b9ab3; }
[data-testid="stMetric"] {
  background: linear-gradient(135deg, #172033, #111827);
  border: 1px solid #2b3b54; padding: 12px; border-radius: 12px;
}
div.stButton > button, div.stDownloadButton > button {
  border-radius: 10px; min-height: 2.7rem; font-weight: 700; letter-spacing: .02em;
}
div.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #0ea5e9, #2563eb); border: 1px solid #38bdf8;
  box-shadow: 0 0 18px rgba(56,189,248,.35);
}
.stTabs [data-baseweb="tab-list"] {
  gap: .4rem; background: rgba(17,26,46,.75); padding: .35rem; border-radius: 12px; border: 1px solid #22324d; flex-wrap: wrap;
}
.stTabs [data-baseweb="tab"] { height: 2.6rem; border-radius: 9px; padding: 0 1.1rem; color: #8b9ab3; font-weight: 600; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, #1e3a5f, #183050); color: #e0f2fe; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

.mono { font-family: 'JetBrains Mono', ui-monospace, Menlo, Consolas, monospace; }
.muted { color: #8b9ab3; }
.sub { font-size: .68rem; color: #7b8aa5; }

.hero {
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;
  padding: 1.3rem 1.6rem; border-radius: 18px; position: relative; overflow: hidden;
  background: linear-gradient(120deg, rgba(19,39,68,.96), rgba(17,24,39,.96) 70%);
  border: 1px solid #29466b; margin-bottom: .9rem;
  box-shadow: 0 10px 40px rgba(2,6,23,.55), inset 0 1px 0 rgba(255,255,255,.04);
}
.hero:after {
  content: ''; position: absolute; left: 0; right: 0; bottom: 0; height: 2px;
  background: linear-gradient(90deg, transparent, #38bdf8, #fb923c, transparent); opacity: .85;
}
.eyebrow { font-size: .72rem; letter-spacing: .22em; color: #7dd3fc; font-weight: 700; }
.title { font-size: 2.05rem; font-weight: 800; color: #f8fafc; margin: .15rem 0; line-height: 1.1; }
.subtitle { color: #9fb0c8; font-size: .95rem; }
.badge {
  display: inline-block; margin: .15rem 0 .15rem .45rem; padding: .3rem .7rem; border-radius: 8px;
  font-size: .68rem; font-weight: 700; letter-spacing: .1em; color: #bae6fd;
  background: rgba(56,189,248,.08); border: 1px solid rgba(56,189,248,.35);
  font-family: 'JetBrains Mono', monospace;
}

.notice { display: flex; align-items: center; gap: .9rem; padding: .8rem 1.1rem; border-radius: 14px; border: 1px solid; margin: .1rem 0 .7rem; }
.notice .n-ico { font-size: 1.5rem; }
.notice .n-title { font-weight: 800; letter-spacing: .06em; font-size: .92rem; }
.notice .n-sub { font-size: .76rem; opacity: .9; margin-top: .1rem; }
.notice.red { color: #ffe4e8; background: rgba(244,63,94,.14); border-color: rgba(244,63,94,.7); box-shadow: 0 0 24px rgba(244,63,94,.35); }
.notice.amber { color: #fef3c7; background: rgba(251,191,36,.11); border-color: rgba(251,191,36,.65); }
.notice.green { color: #d1fae5; background: rgba(52,211,153,.10); border-color: rgba(52,211,153,.55); }

.side-title { font-size: .7rem; font-weight: 800; letter-spacing: .16em; color: #7dd3fc; margin: .2rem 0 .5rem; }
.alert { border: 1px solid; border-radius: 10px; padding: .45rem .6rem; margin-bottom: .4rem; font-size: .76rem; line-height: 1.35; }
.alert b { letter-spacing: .04em; }
.alert.red { color: #fecdd3; background: rgba(244,63,94,.12); border-color: rgba(244,63,94,.55); }
.alert.amber { color: #fde68a; background: rgba(251,191,36,.10); border-color: rgba(251,191,36,.5); }
.alert.green { color: #a7f3d0; background: rgba(52,211,153,.08); border-color: rgba(52,211,153,.4); }
.alert.blue { color: #bae6fd; background: rgba(56,189,248,.08); border-color: rgba(56,189,248,.4); }
.evline { font-size: .7rem; color: #9fb0c8; padding: .15rem 0; border-bottom: 1px dashed #1d2b45; font-family: 'JetBrains Mono', monospace; }

.pill-row { display: flex; flex-wrap: wrap; gap: .7rem; margin: .2rem 0 1rem 0; }
.pill {
  display: inline-flex; align-items: center; gap: .55rem; padding: .45rem .95rem; border-radius: 999px;
  font-weight: 800; font-size: .74rem; letter-spacing: .07em; border: 1px solid;
}
.pill .dot { width: .6rem; height: .6rem; border-radius: 50%; display: inline-block; }
.pill.red { color: #ffe4e8; background: rgba(244,63,94,.15); border-color: rgba(244,63,94,.7);
  box-shadow: 0 0 20px rgba(244,63,94,.45), inset 0 0 12px rgba(244,63,94,.2); }
.pill.red .dot { background: #f43f5e; animation: pulseRed 1.1s infinite; }
.pill.green { color: #d1fae5; background: rgba(52,211,153,.12); border-color: rgba(52,211,153,.65);
  box-shadow: 0 0 20px rgba(52,211,153,.35), inset 0 0 12px rgba(52,211,153,.15); }
.pill.green .dot { background: #34d399; box-shadow: 0 0 10px #34d399; }
.pill.amber { color: #fef3c7; background: rgba(251,191,36,.12); border-color: rgba(251,191,36,.65);
  box-shadow: 0 0 20px rgba(251,191,36,.32), inset 0 0 12px rgba(251,191,36,.14); }
.pill.amber .dot { background: #fbbf24; box-shadow: 0 0 10px #fbbf24; }
.pill.blue { color: #e0f2fe; background: rgba(56,189,248,.12); border-color: rgba(56,189,248,.6);
  box-shadow: 0 0 20px rgba(56,189,248,.3), inset 0 0 12px rgba(56,189,248,.14); }
.pill.blue .dot { background: #38bdf8; box-shadow: 0 0 10px #38bdf8; }
@keyframes pulseRed {
  0% { box-shadow: 0 0 0 0 rgba(244,63,94,.85); }
  70% { box-shadow: 0 0 0 10px rgba(244,63,94,0); }
  100% { box-shadow: 0 0 0 0 rgba(244,63,94,0); }
}
@media (prefers-reduced-motion: reduce) { .pill.red .dot { animation: none; } }

.panel {
  background: linear-gradient(160deg, rgba(20,31,53,.93), rgba(14,23,38,.93));
  border: 1px solid #22324d; border-radius: 16px; padding: 1rem 1.05rem;
  box-shadow: 0 8px 28px rgba(2,6,23,.45), inset 0 1px 0 rgba(255,255,255,.035);
}
.panel-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: .7rem; }
.panel-title { font-size: .72rem; font-weight: 800; letter-spacing: .16em; color: #7dd3fc; }
.tag { font-size: .62rem; font-weight: 700; letter-spacing: .12em; padding: .15rem .5rem; border-radius: 6px;
  font-family: 'JetBrains Mono', monospace; }
.tag.live { color: #6ee7b7; background: rgba(52,211,153,.1); border: 1px solid rgba(52,211,153,.4); }
.tag.sim { color: #fde68a; background: rgba(251,191,36,.1); border: 1px solid rgba(251,191,36,.4); }

.scada, .scada th, .scada td { background: transparent !important; border-left: none !important; border-right: none !important; }
.scada { width: 100%; border-collapse: collapse; margin: 0; }
.scada th { font-size: .62rem; letter-spacing: .12em; color: #7b8aa5; font-weight: 700; text-align: left;
  padding: .25rem .3rem .45rem; border-bottom: 1px solid #22324d !important; }
.scada td { padding: .55rem .3rem; border-bottom: 1px solid rgba(34,50,77,.55) !important; vertical-align: middle; font-size: .82rem; color: #e5e7eb; }
.scada tr:last-child td { border-bottom: none !important; }
.bar { height: 7px; border-radius: 5px; background: #0b1424; border: 1px solid #1d2b45; overflow: hidden; min-width: 60px; margin-bottom: .25rem; }
.fill { height: 100%; border-radius: 5px; }
.fill.green { background: linear-gradient(90deg, #059669, #34d399); box-shadow: 0 0 8px rgba(52,211,153,.6); }
.fill.amber { background: linear-gradient(90deg, #d97706, #fbbf24); box-shadow: 0 0 8px rgba(251,191,36,.6); }
.fill.red { background: linear-gradient(90deg, #e11d48, #fb7185); box-shadow: 0 0 8px rgba(244,63,94,.7); }
.chip { display: inline-block; padding: .1rem .5rem; border-radius: 6px; font-size: .6rem; font-weight: 800;
  letter-spacing: .09em; border: 1px solid; font-family: 'JetBrains Mono', monospace; }
.chip.green { color: #6ee7b7; border-color: rgba(52,211,153,.5); background: rgba(52,211,153,.1); }
.chip.amber { color: #fde68a; border-color: rgba(251,191,36,.5); background: rgba(251,191,36,.1); }
.chip.red { color: #fda4af; border-color: rgba(244,63,94,.6); background: rgba(244,63,94,.12); }
.chip.blue { color: #7dd3fc; border-color: rgba(56,189,248,.5); background: rgba(56,189,248,.1); }
.chip.gray { color: #94a3b8; border-color: rgba(148,163,184,.35); background: rgba(148,163,184,.08); }

.kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: .7rem; margin: .2rem 0 1rem; }
.kpi { padding: .75rem .9rem; border-radius: 12px; background: linear-gradient(135deg, #172033, #111827); border: 1px solid #2b3b54; }
.kpi-label { font-size: .62rem; letter-spacing: .13em; color: #7b8aa5; font-weight: 700; text-transform: uppercase; }
.kpi-value { font-size: 1.4rem; font-weight: 800; color: #f1f5f9; font-family: 'JetBrains Mono', monospace; margin-top: .15rem; }
.kpi-sub { font-size: .7rem; color: #8b9ab3; }
.kpi.green .kpi-value { color: #6ee7b7; } .kpi.amber .kpi-value { color: #fde68a; }
.kpi.red .kpi-value { color: #fda4af; } .kpi.blue .kpi-value { color: #7dd3fc; }

.wind-wrap { display: flex; justify-content: center; margin: .1rem 0 .3rem; }
.legend-row { display: flex; gap: .9rem; justify-content: center; flex-wrap: wrap; font-size: .68rem; color: #9fb0c8; margin-bottom: .7rem; }
.ldot { display: inline-block; width: 18px; height: 3px; border-radius: 2px; margin-right: .35rem; vertical-align: middle; }
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: .5rem; }
.stat { background: rgba(11,20,36,.7); border: 1px solid #1d2b45; border-radius: 10px; padding: .5rem .65rem; }
.stat-label { font-size: .58rem; letter-spacing: .13em; color: #7b8aa5; font-weight: 800; }
.stat-value { font-size: .9rem; color: #f1f5f9; font-weight: 700; margin-top: .1rem; }

.ci { background: rgba(11,20,36,.65); border: 1px solid #1d2b45; border-radius: 11px; padding: .55rem .75rem; margin-bottom: .5rem; }
.ci-top { display: flex; justify-content: space-between; align-items: baseline; }
.ci-label { font-size: .6rem; font-weight: 800; letter-spacing: .13em; color: #7b8aa5; }
.ci-est { font-size: 1.05rem; font-weight: 700; color: #f1f5f9; }
.ci-track { position: relative; height: 8px; border-radius: 6px; background: #0b1424; border: 1px solid #1d2b45; margin: .5rem 0 .35rem; }
.ci-band { position: absolute; top: 0; bottom: 0; border-radius: 6px;
  background: linear-gradient(90deg, rgba(56,189,248,.35), rgba(52,211,153,.6)); box-shadow: 0 0 10px rgba(56,189,248,.35); }
.ci-tick { position: absolute; top: -4px; width: 3px; height: 14px; border-radius: 2px; background: #34d399;
  box-shadow: 0 0 8px #34d399; transform: translateX(-1px); }
.ci-truth { position: absolute; top: -3px; width: 8px; height: 8px; border: 2px solid #f8fafc; transform: translateX(-4px) rotate(45deg); border-radius: 2px; }
.ci-foot { display: flex; justify-content: space-between; font-size: .66rem; color: #8b9ab3; gap: .5rem; }
.gauge-row { display: flex; justify-content: space-between; gap: .3rem; margin-top: .4rem; }
.gauge { flex: 1; text-align: center; }

.hud { position: relative; border-radius: 16px; padding: .8rem .9rem 1rem; background: #0e1726; border: 1px solid #28405f;
  box-shadow: 0 0 0 1px rgba(56,189,248,.06), 0 0 45px rgba(56,189,248,.08), 0 16px 50px rgba(2,6,23,.6); margin: 1.1rem 0 .8rem; }
.hud:before, .hud:after { content: ''; position: absolute; width: 26px; height: 26px; border: 2px solid #38bdf8; opacity: .8; pointer-events: none; }
.hud:before { top: 8px; left: 8px; border-right: none; border-bottom: none; border-top-left-radius: 10px; }
.hud:after { bottom: 8px; right: 8px; border-left: none; border-top: none; border-bottom-right-radius: 10px; }
.hud-head { display: flex; justify-content: space-between; align-items: center; padding: .1rem .9rem .6rem; flex-wrap: wrap; gap: .4rem; }
.hud-title { font-size: .74rem; font-weight: 800; letter-spacing: .16em; color: #7dd3fc; }
.hud-right { font-size: .66rem; letter-spacing: .1em; color: #8b9ab3; font-family: 'JetBrains Mono', monospace; }
.map-img { display: block; width: 100%; height: auto; border-radius: 10px; }

.callout { padding: .75rem 1rem; border-radius: 12px; font-size: .88rem; border: 1px solid; margin: .5rem 0; line-height: 1.45; }
.callout.info { color: #bae6fd; background: rgba(56,189,248,.08); border-color: rgba(56,189,248,.35); }
.callout.warn { color: #fde68a; background: rgba(251,191,36,.08); border-color: rgba(251,191,36,.4); }
.callout.ok { color: #a7f3d0; background: rgba(52,211,153,.08); border-color: rgba(52,211,153,.4); }
.callout.err { color: #fecdd3; background: rgba(244,63,94,.08); border-color: rgba(244,63,94,.45); }
</style>
"""
