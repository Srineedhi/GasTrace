"""Self-contained in-browser (canvas/JS) interactive twin."""

from __future__ import annotations

import json


# ---------------------- Interactive in-browser twin --------------------------
# Self-contained HTML/JS (canvas). Left tool rail (Settings / Source / Mobile / Alerts), fullscreen,
# live simulation, mobile sensor with active-sensing auto-guide, live alerts and notification bar.
INTERACTIVE_HTML = r'''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
:root{--bg:#0b1220;--line:#22324d;--text:#e5e7eb;--muted:#8b9ab3;--cyan:#38bdf8;--orange:#fb923c;--green:#34d399;--red:#f43f5e;--amber:#fbbf24}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:transparent;color:var(--text);font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif}
.mono{font-family:'JetBrains Mono',ui-monospace,Menlo,Consolas,monospace}
#app{padding:2px}
#app.fs{background:#0b1220;padding:12px;height:100vh;overflow:auto}
.notice{display:flex;align-items:center;justify-content:space-between;gap:.8rem;padding:.65rem 1rem;border-radius:14px;border:1px solid;margin:0 0 .6rem}
.notice .n-main{display:flex;align-items:center;gap:.8rem;min-width:0}
.notice .n-ico{font-size:1.35rem}
.n-title{font-weight:800;letter-spacing:.06em;font-size:.84rem}
.n-sub{font-size:.7rem;opacity:.92;margin-top:.1rem}
.notice.red{color:#ffe4e8;background:rgba(244,63,94,.14);border-color:rgba(244,63,94,.7);box-shadow:0 0 22px rgba(244,63,94,.35)}
.notice.amber{color:#fef3c7;background:rgba(251,191,36,.11);border-color:rgba(251,191,36,.65)}
.notice.green{color:#d1fae5;background:rgba(52,211,153,.10);border-color:rgba(52,211,153,.55)}
.bell{position:relative;white-space:nowrap}
.badge{display:inline-block;min-width:18px;padding:0 5px;border-radius:9px;background:#f43f5e;color:#fff;font-size:.62rem;font-weight:800;text-align:center;margin-left:4px}
.badge.zero{background:#334155}
.pill-row{display:flex;flex-wrap:wrap;gap:.5rem;margin:0 0 .7rem}
.pill{display:inline-flex;align-items:center;gap:.5rem;padding:.35rem .8rem;border-radius:999px;font-weight:800;font-size:.66rem;letter-spacing:.06em;border:1px solid}
.pill .dot{width:.5rem;height:.5rem;border-radius:50%;display:inline-block}
.pill.red{color:#ffe4e8;background:rgba(244,63,94,.15);border-color:rgba(244,63,94,.7);box-shadow:0 0 18px rgba(244,63,94,.45),inset 0 0 12px rgba(244,63,94,.2)}
.pill.red .dot{background:#f43f5e;animation:pr 1.1s infinite}
.pill.green{color:#d1fae5;background:rgba(52,211,153,.12);border-color:rgba(52,211,153,.65);box-shadow:0 0 18px rgba(52,211,153,.35),inset 0 0 12px rgba(52,211,153,.15)}
.pill.green .dot{background:#34d399;box-shadow:0 0 10px #34d399}
.pill.amber{color:#fef3c7;background:rgba(251,191,36,.12);border-color:rgba(251,191,36,.65);box-shadow:0 0 18px rgba(251,191,36,.32),inset 0 0 12px rgba(251,191,36,.14)}
.pill.amber .dot{background:#fbbf24;box-shadow:0 0 10px #fbbf24}
.pill.blue{color:#e0f2fe;background:rgba(56,189,248,.12);border-color:rgba(56,189,248,.6);box-shadow:0 0 18px rgba(56,189,248,.3),inset 0 0 12px rgba(56,189,248,.14)}
.pill.blue .dot{background:#38bdf8;box-shadow:0 0 10px #38bdf8}
@keyframes pr{0%{box-shadow:0 0 0 0 rgba(244,63,94,.85)}70%{box-shadow:0 0 0 9px rgba(244,63,94,0)}100%{box-shadow:0 0 0 0 rgba(244,63,94,0)}}
@media (prefers-reduced-motion:reduce){.pill.red .dot{animation:none}}
.shell{display:flex;gap:12px;align-items:flex-start;flex-wrap:nowrap}
.rail{flex:0 0 58px;display:flex;flex-direction:column;gap:8px;padding:8px 6px;border-radius:14px;background:rgba(17,26,46,.85);border:1px solid #22324d;position:sticky;top:0}
.rb{display:flex;flex-direction:column;align-items:center;gap:2px;padding:.45rem .1rem;font-size:1.05rem;line-height:1;position:relative;background:transparent;border:1px solid transparent;color:#9fb0c8;border-radius:10px;cursor:pointer}
.rb span{font-size:.5rem;letter-spacing:.06em;font-weight:700;color:#8b9ab3}
.rb:hover{box-shadow:none;background:rgba(56,189,248,.08)}
.rb.on{background:linear-gradient(135deg,#1e3a5f,#183050);border-color:#38bdf8;color:#e0f2fe}
.rb i{position:absolute;top:2px;right:6px;background:#f43f5e;color:#fff;border-radius:8px;font-style:normal;font-size:.55rem;font-weight:800;padding:0 4px;display:none}
.drawer{flex:0 0 0;width:0;overflow:hidden;transition:width .18s ease}
.drawer.open{flex:0 0 310px;width:310px}
.drawer .inner{width:310px;display:flex;flex-direction:column;gap:12px}
.pn{display:none}.pn.on{display:block}
.stage{flex:1 1 520px;min-width:0}
.hud{position:relative;border-radius:16px;padding:10px;background:#0e1726;border:1px solid #28405f;box-shadow:0 0 0 1px rgba(56,189,248,.06),0 0 40px rgba(56,189,248,.08),0 14px 40px rgba(2,6,23,.6)}
.hud:before,.hud:after{content:'';position:absolute;width:24px;height:24px;border:2px solid #38bdf8;opacity:.8;pointer-events:none}
.hud:before{top:6px;left:6px;border-right:none;border-bottom:none;border-top-left-radius:10px}
.hud:after{bottom:6px;right:6px;border-left:none;border-top:none;border-bottom-right-radius:10px}
.hud-head{display:flex;justify-content:space-between;align-items:center;gap:.5rem;flex-wrap:wrap;padding:2px 10px 8px}
.hud-title{font-size:.64rem;font-weight:800;letter-spacing:.14em;color:#7dd3fc}
.hud-tools{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.hud-right{font-size:.6rem;letter-spacing:.06em;color:#8b9ab3}
canvas{display:block;touch-action:none;border-radius:10px;margin:0 auto}
.legend{display:flex;flex-wrap:wrap;gap:.4rem 1rem;font-size:.66rem;color:#9fb0c8;padding:8px 10px 2px}
.legend i{display:inline-block;width:16px;height:3px;border-radius:2px;margin-right:.35rem;vertical-align:middle}
.side{flex:0 1 320px;min-width:260px;display:flex;flex-direction:column;gap:12px}
.card{background:linear-gradient(160deg,rgba(20,31,53,.93),rgba(14,23,38,.93));border:1px solid #22324d;border-radius:14px;padding:12px 14px;box-shadow:0 8px 28px rgba(2,6,23,.45)}
.card h4{margin:0 0 .6rem;font-size:.66rem;font-weight:800;letter-spacing:.16em;color:#7dd3fc}
.ctl{display:grid;grid-template-columns:1fr auto;align-items:center;gap:2px 8px;margin-bottom:.45rem;font-size:.74rem;color:#cbd5e1}
.ctl output{font-family:'JetBrains Mono',monospace;color:#f1f5f9;font-size:.74rem}
.ctl input[type=range]{grid-column:1/3;width:100%;accent-color:#38bdf8}
select{background:#0b1424;color:#e5e7eb;border:1px solid #28405f;border-radius:8px;padding:.25rem .4rem;font-size:.74rem}
.btns{display:flex;gap:8px;flex-wrap:wrap;margin-top:.4rem}
button{background:linear-gradient(135deg,#1e3a5f,#183050);color:#e0f2fe;border:1px solid #38bdf8;border-radius:9px;padding:.4rem .75rem;font-weight:700;font-size:.72rem;cursor:pointer;font-family:inherit}
button:hover{box-shadow:0 0 14px rgba(56,189,248,.4)}
button.on{background:linear-gradient(135deg,#0f766e,#115e59);border-color:#34d399}
button.warn{border-color:#fbbf24;color:#fef3c7}
.layers{display:flex;flex-wrap:wrap;gap:.3rem .8rem;font-size:.72rem;color:#cbd5e1;margin-top:.3rem}
.layers label,.chk{display:flex;align-items:center;gap:.3rem;cursor:pointer;font-size:.72rem;color:#cbd5e1}
table{width:100%;border-collapse:collapse;font-size:.74rem}
th{font-size:.58rem;letter-spacing:.12em;color:#7b8aa5;text-align:left;padding:.15rem .25rem .35rem;border-bottom:1px solid #22324d}
td{padding:.32rem .25rem;border-bottom:1px solid rgba(34,50,77,.55);font-family:'JetBrains Mono',monospace;color:#e5e7eb}
td:first-child{color:#8b9ab3;font-family:'Inter',sans-serif;font-weight:600}
tr:last-child td{border-bottom:none}
.ok{color:#34d399}.bad{color:#fb7185}
.vane-wrap{display:flex;justify-content:center}
.small{font-size:.66rem;color:#8b9ab3;line-height:1.4}
.scn{font-size:.7rem;color:#bae6fd;background:rgba(56,189,248,.08);border:1px solid rgba(56,189,248,.3);border-radius:8px;padding:.35rem .6rem;margin-top:.5rem;font-family:'JetBrains Mono',monospace}
.chip{display:inline-block;padding:.05rem .45rem;border-radius:6px;font-size:.58rem;font-weight:800;letter-spacing:.08em;border:1px solid;font-family:'JetBrains Mono',monospace}
.chip.green{color:#6ee7b7;border-color:rgba(52,211,153,.5);background:rgba(52,211,153,.1)}
.chip.amber{color:#fde68a;border-color:rgba(251,191,36,.5);background:rgba(251,191,36,.1)}
.chip.red{color:#fda4af;border-color:rgba(244,63,94,.6);background:rgba(244,63,94,.12)}
.chip.blue{color:#7dd3fc;border-color:rgba(56,189,248,.5);background:rgba(56,189,248,.1)}
.disp{border-radius:10px;padding:.5rem .65rem;font-size:.72rem;line-height:1.4;border:1px solid}
.disp.red{color:#fecdd3;background:rgba(244,63,94,.1);border-color:rgba(244,63,94,.5)}
.disp.amber{color:#fde68a;background:rgba(251,191,36,.08);border-color:rgba(251,191,36,.45)}
.disp.green{color:#a7f3d0;background:rgba(52,211,153,.07);border-color:rgba(52,211,153,.4)}
.feed{max-height:230px;overflow:auto;display:flex;flex-direction:column;gap:3px}
.ev{font-size:.66rem;font-family:'JetBrains Mono',monospace;padding:.2rem .4rem;border-left:3px solid #38bdf8;background:rgba(11,20,36,.6);border-radius:4px;color:#cbd5e1}
.ev.red{border-color:#f43f5e}.ev.amber{border-color:#fbbf24}.ev.green{border-color:#34d399}
.ev b{color:#7b8aa5;font-weight:500;margin-right:.4rem}
@media (max-width:900px){.shell{flex-wrap:wrap}.side{flex:1 1 100%}.drawer.open{flex:1 1 100%;width:100%}.drawer .inner{width:100%}}
</style>
</head>
<body>
<div id="app">
<div class="notice green" id="notice">
  <div class="n-main"><span class="n-ico" id="n_ico">✔</span><div><div class="n-title" id="n_title">Twin starting…</div><div class="n-sub mono" id="n_sub"></div></div></div>
  <button id="b_bell" class="bell" title="Open live alerts">🔔 Alerts<span id="bellN" class="badge zero">0</span></button>
</div>
<div class="pill-row" id="pills"></div>
<div class="shell">
  <nav class="rail">
    <button class="rb" data-p="settings" title="Settings">⚙<span>SETTINGS</span></button>
    <button class="rb" data-p="source" title="Source control">◎<span>SOURCE</span></button>
    <button class="rb" data-p="mobile" title="Mobile sensor">🛰<span>MOBILE</span></button>
    <button class="rb" data-p="alerts" title="Alerts">🔔<span>ALERTS</span><i id="railBadge">0</i></button>
  </nav>
  <aside class="drawer" id="drawer"><div class="inner">
    <div class="pn card" id="pn_settings">
      <h4>SETTINGS · WIND &amp; SENSING</h4>
      <div class="ctl"><span>Wind FROM (°)</span><output id="o_dir"></output><input type="range" id="s_dir" min="0" max="359" step="1"></div>
      <div class="ctl"><span>Wind speed (m/s)</span><output id="o_u"></output><input type="range" id="s_u" min="0.5" max="10" step="0.5"></div>
      <div class="ctl"><span>Wind-direction telemetry σ (°)</span><output id="o_dsd"></output><input type="range" id="s_dsd" min="1" max="60" step="1"></div>
      <div class="ctl"><span>Wind-speed telemetry σ (m/s)</span><output id="o_usd"></output><input type="range" id="s_usd" min="0.1" max="3" step="0.1"></div>
      <div class="ctl"><span>Sensor noise</span><output id="o_n"></output><input type="range" id="s_n" min="0.05" max="2" step="0.05"></div>
      <div class="ctl"><span>Alarm threshold</span><output id="o_t"></output><input type="range" id="s_t" min="0.2" max="5" step="0.1"></div>
      <div class="ctl"><span>Particles</span><select id="s_p"><option>1000</option><option>2000</option><option>4000</option><option>6000</option><option>8000</option></select></div>
      <div class="ctl"><span>Simulation speed</span><select id="s_sp"><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option><option value="4">4×</option></select></div>
      <div class="layers">
        <label><input type="checkbox" id="L_plume" checked>True plume</label>
        <label><input type="checkbox" id="L_post" checked>Posterior</label>
        <label><input type="checkbox" id="L_axis" checked>Spread lines</label>
        <label><input type="checkbox" id="L_box" checked>95% box</label>
        <label><input type="checkbox" id="L_cloud">Particles</label>
        <label><input type="checkbox" id="L_info" checked>Info-gain map</label>
      </div>
      <div class="btns"><button id="b_noise">New noise sample</button><button id="b_reset">Reset scenario</button></div>
      <div class="scn" id="scn"></div>
    </div>
    <div class="pn card" id="pn_source">
      <h4>SOURCE CONTROL · SIMULATED LEAK</h4>
      <div class="ctl"><span>Leak X (m)</span><output id="o_lx"></output><input type="range" id="s_lx" min="0" max="100" step="0.5"></div>
      <div class="ctl"><span>Leak Y (m)</span><output id="o_ly"></output><input type="range" id="s_ly" min="0" max="100" step="0.5"></div>
      <div class="ctl"><span>Release rate Q (relative)</span><output id="o_q"></output><input type="range" id="s_q" min="10" max="100" step="1"></div>
      <label class="chk"><input type="checkbox" id="c_move">Moving leak during simulation (drifts ~2 m/s)</label>
      <label class="chk"><input type="checkbox" id="c_veer" checked>Wind veer + turbulence during simulation</label>
      <div class="btns"><button id="b_simS">▶ Simulate</button><button id="b_center">Centre leak</button></div>
      <div class="small" style="margin-top:.5rem">Tip: drag the red ★ on the map for the same effect. The estimator never sees the true source.</div>
    </div>
    <div class="pn card" id="pn_mobile">
      <h4>MOBILE SENSOR · ACTIVE SENSING</h4>
      <label class="chk"><input type="checkbox" id="m_on">Deploy mobile sensor (M)</label>
      <div class="ctl" style="margin-top:.4rem"><span>Mobile X (m)</span><output id="o_mx"></output><input type="range" id="m_x" min="0" max="100" step="0.5"></div>
      <div class="ctl"><span>Mobile Y (m)</span><output id="o_my"></output><input type="range" id="m_y" min="0" max="100" step="0.5"></div>
      <div class="ctl"><span>Travel speed (m/s)</span><output id="o_msp"></output><input type="range" id="m_speed" min="2" max="30" step="1"></div>
      <div class="ctl"><span>Mission length (samples)</span><output id="o_mlen"></output><input type="range" id="m_len" min="1" max="8" step="1"></div>
      <div class="btns">
        <button id="b_take">Take sample here</button>
        <button id="b_go">Go to suggested point</button>
        <button id="b_auto">Auto-guide: OFF</button>
        <button id="b_clear" class="warn">Clear trail</button>
      </div>
      <div class="scn" id="m_stat">Mobile sensor not deployed.</div>
      <div class="small" style="margin-top:.5rem">The suggested point is where the posterior-predictive variance is highest (heuristic, not a proven optimum, no obstacle-aware routing). Each sample is assimilated by the particle filter together with the fixed sensors.</div>
    </div>
    <div class="pn card" id="pn_alerts">
      <h4>ALERTS · LIVE SENSOR STATUS</h4>
      <table><thead><tr><th>NODE</th><th>READING</th><th>LEVEL</th><th>Δ EST</th></tr></thead><tbody id="al_sensors"></tbody></table>
      <div style="margin:.6rem 0 .4rem" class="disp green" id="al_dispatch"></div>
      <h4 style="margin-top:.7rem">EVENT FEED (WHAT CHANGED)</h4>
      <div class="feed" id="al_feed"></div>
    </div>
  </div></aside>
  <div class="stage" id="stage">
    <div class="hud">
      <div class="hud-head">
        <span class="hud-title">INTERACTIVE TOPOGRAPHIC MAP · DRAG ★ LEAK · ■ SENSORS · ▲ MOBILE</span>
        <span class="hud-tools"><span class="hud-right mono" id="cursorTxt">CURSOR — move over the map</span>
          <button id="b_sim">▶ Simulate</button><button id="b_fs" title="Full screen">⛶ Full screen</button></span>
      </div>
      <canvas id="map"></canvas>
      <div class="legend">
        <span><i style="background:#f43f5e"></i>True leak ★ and plume axis</span>
        <span><i style="background:#34d399"></i>Estimated source ✕ and spread direction</span>
        <span><i style="background:#fb923c"></i>Posterior probability</span>
        <span><i style="background:#8c2981"></i>True plume (simulated)</span>
        <span><i style="background:#38bdf8"></i>Fixed sensors</span>
        <span><i style="background:#fbbf24"></i>Mobile sensor / trail / next sample</span>
      </div>
    </div>
  </div>
  <div class="side">
    <div class="card">
      <h4>WIND VANE · DRAG TO SET WIND DIRECTION</h4>
      <div class="vane-wrap"><canvas id="vane" width="210" height="210" style="width:210px;height:210px"></canvas></div>
      <div class="small" style="text-align:center;margin-top:.3rem"><span style="color:#f8fafc">white</span> true flow · <span style="color:#38bdf8">cyan</span> noisy telemetry · <span style="color:#34d399">green</span> detected by the twin</div>
    </div>
    <div class="card">
      <h4>DETECTION READOUT</h4>
      <table>
        <thead><tr><th></th><th>TRUE (SIM)</th><th>ESTIMATED</th><th>95% CI</th></tr></thead>
        <tbody id="tb"></tbody>
      </table>
      <div class="small" style="margin-top:.5rem">Truth is shown for evaluation only. The estimator sees the sensor readings and noisy wind telemetry, never the true source or true wind.</div>
    </div>
  </div>
</div>
</div>
<script>
(function(){
"use strict";
const CFG = __CONFIG__;

//--CORE-START
const SITE = 100;
function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
function makeRng(seed){
  const r=mulberry32(seed>>>0); let spare=null;
  return {u:r, n:function(){
    if(spare!==null){const s=spare;spare=null;return s;}
    let u=0; while(u===0)u=r(); const v=r(); const m=Math.sqrt(-2*Math.log(u));
    spare=m*Math.sin(2*Math.PI*v); return m*Math.cos(2*Math.PI*v);}};
}
function clamp(v,a,b){return Math.min(b,Math.max(a,v));}
function mod360(a){return ((a%360)+360)%360;}
function plume(xs,ys,xq,yq,q,u,dirDeg,h){
  h=(h===undefined)?1:h;
  const uu=Math.max(u,0.1), th=mod360(dirDeg)*Math.PI/180;
  const dx=xs-xq, dy=ys-yq;
  const xd=-dx*Math.sin(th)-dy*Math.cos(th);
  if(xd<=0.1) return 0;
  const yc=dx*Math.cos(th)-dy*Math.sin(th);
  const sy=Math.max(0.08*xd/Math.sqrt(1+0.0001*xd),0.25);
  const sz=Math.max(0.06*xd/Math.sqrt(1+0.0015*xd),0.25);
  const vert=2*Math.exp(-0.5*(h/sz)*(h/sz));
  return q/(2*Math.PI*uu*sy*sz)*Math.exp(-0.5*(yc/sy)*(yc/sy))*vert;
}
function wQuantiles(vals,w,qs){
  const n=vals.length, idx=new Array(n); for(let i=0;i<n;i++)idx[i]=i;
  idx.sort(function(a,b){return vals[a]-vals[b];});
  const cum=new Float64Array(n); let c=0;
  for(let i=0;i<n;i++){c+=w[idx[i]];cum[i]=c;}
  return qs.map(function(q){
    const t=q*c; let i=0; while(i<n-1&&cum[i]<t)i++;
    if(i===0) return vals[idx[0]];
    const c0=cum[i-1],c1=cum[i],v0=vals[idx[i-1]],v1=vals[idx[i]];
    return c1>c0? v0+(v1-v0)*(t-c0)/(c1-c0) : v1;
  });
}
function runPF(P){
  const rng=makeRng(P.seed), n=P.n|0, sig=Math.max(P.noise,1e-3);
  const uSd=Math.max(P.uSd,0.05), dSd=Math.max(P.dSd,1.0);
  let px=new Float64Array(n),py=new Float64Array(n),pq=new Float64Array(n),pu=new Float64Array(n),pd=new Float64Array(n);
  for(let i=0;i<n;i++){px[i]=rng.u()*SITE;py[i]=rng.u()*SITE;pq[i]=10+rng.u()*90;}
  for(let i=0;i<n;i++){pu[i]=clamp(P.obsU+uSd*rng.n(),0.5,12);}
  for(let i=0;i<n;i++){pd[i]=mod360(P.obsD+dSd*rng.n());}
  let w=new Float64Array(n).fill(1/n);
  const ll=new Float64Array(n);
  for(let s=0;s<P.sensors.length;s++){
    const sn=P.sensors[s]; let mx=-Infinity;
    for(let i=0;i<n;i++){
      const pred=plume(sn.x,sn.y,px[i],py[i],pq[i],pu[i],pd[i])+sn.off;
      const r=(P.readings[s]-pred)/sig; ll[i]=-0.5*r*r; if(ll[i]>mx)mx=ll[i];
    }
    let tot=0;
    for(let i=0;i<n;i++){w[i]*=Math.exp(ll[i]-mx); tot+=w[i];}
    if(!(tot>1e-300)||!isFinite(tot)){w.fill(1/n);} else {for(let i=0;i<n;i++)w[i]/=tot;}
    let s2=0; for(let i=0;i<n;i++)s2+=w[i]*w[i];
    if(1/s2<0.45*n && s<P.sensors.length-1){
      const u0=rng.u(); const nx=new Float64Array(n),ny=new Float64Array(n),nq=new Float64Array(n),nu=new Float64Array(n),nd=new Float64Array(n);
      let c=w[0],j=0;
      for(let i=0;i<n;i++){
        const pos=(u0+i)/n; while(pos>c&&j<n-1){j++;c+=w[j];}
        nx[i]=px[j];ny[i]=py[j];nq[i]=pq[j];nu[i]=pu[j];nd[i]=pd[j];
      }
      px=nx;py=ny;pq=nq;pu=nu;pd=nd; w.fill(1/n);
    }
  }
  let s2=0,mxm=0,mym=0,mqm=0,mum=0,ss=0,cc=0;
  for(let i=0;i<n;i++){
    s2+=w[i]*w[i]; mxm+=w[i]*px[i]; mym+=w[i]*py[i]; mqm+=w[i]*pq[i]; mum+=w[i]*pu[i];
    const a=pd[i]*Math.PI/180; ss+=w[i]*Math.sin(a); cc+=w[i]*Math.cos(a);
  }
  const dirm=mod360(Math.atan2(ss,cc)*180/Math.PI);
  const delta=new Float64Array(n);
  for(let i=0;i<n;i++){delta[i]=mod360(pd[i]-dirm+180)-180;}
  const qs=[0.025,0.975];
  const dq=wQuantiles(delta,w,qs);
  return {x:mxm,y:mym,q:mqm,u:mum,dir:dirm,ess:1/s2,px:px,py:py,pq:pq,pu:pu,pd:pd,w:w,
    ci:{x:wQuantiles(px,w,qs),y:wQuantiles(py,w,qs),q:wQuantiles(pq,w,qs),u:wQuantiles(pu,w,qs),
        th:[mod360(dirm+dq[0]),mod360(dirm+dq[1])],half:(dq[1]-dq[0])/2}};
}
// Active sensing: posterior-predictive variance / noise^2 on a candidate grid (heuristic).
function suggestPoint(R,noise,occupied){
  const n=R.w.length, M=Math.min(400,n), G=19;
  const idx=new Int32Array(M); let c=R.w[0], j=0;
  for(let m=0;m<M;m++){const pos=(m+0.5)/M; while(pos>c&&j<n-1){j++;c+=R.w[j];} idx[m]=j;}
  const sc=new Float64Array(G*G); let best=-1,bx=50,by=50,mx=0;
  for(let gy=0;gy<G;gy++)for(let gx=0;gx<G;gx++){
    const X=5+gx*5,Y=5+gy*5; let blocked=false;
    for(let k=0;k<occupied.length;k++){if(Math.hypot(occupied[k].x-X,occupied[k].y-Y)<6){blocked=true;break;}}
    if(blocked){sc[gy*G+gx]=-1;continue;}
    let s=0,s2=0;
    for(let m=0;m<M;m++){const q=idx[m]; const p=plume(X,Y,R.px[q],R.py[q],R.pq[q],R.pu[q],R.pd[q]); s+=p; s2+=p*p;}
    const v=Math.max(s2/M-(s/M)*(s/M),0)/(noise*noise+1e-9);
    sc[gy*G+gx]=v; if(v>mx)mx=v; if(v>best){best=v;bx=X;by=Y;}
  }
  return {G:G,sc:sc,max:mx,best:{x:bx,y:by,score:Math.max(best,0)}};
}
//--CORE-END

const $=function(id){return document.getElementById(id);};
const BG="#0e1726", CYAN="#38bdf8", GREEN="#34d399", RED="#f43f5e", AMBER="#fbbf24", ORANGE="#fb923c";
const MOFF=0.05, MAXTRAIL=8, LN=["NORMAL","WARN","ALARM"];
const INIT=JSON.parse(JSON.stringify(CFG));
const S={
  src:{x:CFG.leak_x,y:CFG.leak_y}, q:CFG.strength, u:CFG.wind_speed, dir:CFG.wind_from,
  uSd:CFG.wind_speed_sd, dSd:CFG.wind_dir_sd, noise:CFG.noise, thr:CFG.threshold, n:CFG.n_particles,
  sensors:CFG.sensors.map(function(s){return {x:s.x,y:s.y,off:s.off,name:s.name};}),
  z:[], zWu:0, zWd:0, nc:0, readings:[], all:[], obsU:0, obsD:0, res:null, latency:0, conf:0,
  mob:{on:CFG.mobile_on,x:CFG.mobile_x,y:CFG.mobile_y,tx:null,ty:null,speed:10,len:CFG.mobile_len,auto:false,zm:0,cnt:0,trail:[]},
  sim:{on:false,speed:1,move:false,veer:true,vx:1.4,vy:0.9,tick:0,rng:makeRng(CFG.seed+99)},
  sug:null, events:[], prevLv:{}, prevPred:null, lastEst:null, panel:null
};
function regenNoise(){
  const r=makeRng(CFG.seed*7+13+S.nc*101);
  S.z=S.sensors.map(function(){return r.n();}); S.zWu=r.n(); S.zWd=r.n(); S.mob.zm=r.n();
}
regenNoise();
function hhmmss(){return new Date().toLocaleTimeString([], {hour12:false});}
function logEv(level,msg){
  S.events.push({t:hhmmss(),level:level,msg:msg});
  if(S.events.length>60)S.events.shift();
}

// ---------- layout / canvases ----------
const cv=$("map"), ctx=cv.getContext("2d"), stage=$("stage");
const vcv=$("vane"), vctx=vcv.getContext("2d");
let cw=700,ch=740,padL=48,padR=14,padT=14,padB=40,SZ=640,dpr=window.devicePixelRatio||1;
function layout(){
  const fs=!!document.fullscreenElement;
  let sz=stage.clientWidth-22-padL-padR;
  if(fs){sz=Math.min(sz,window.innerHeight-250-padT-padB);}
  else{sz=Math.min(sz,(CFG.expanded?1000:770)-padL-padR);}
  SZ=Math.max(sz,260); cw=SZ+padL+padR; ch=SZ+padT+padB;
  dpr=window.devicePixelRatio||1;
  cv.width=Math.round(cw*dpr); cv.height=Math.round(ch*dpr);
  cv.style.width=cw+"px"; cv.style.height=ch+"px";
  ctx.setTransform(dpr,0,0,dpr,0,0);
  vcv.width=Math.round(210*dpr); vcv.height=Math.round(210*dpr);
  vctx.setTransform(dpr,0,0,dpr,0,0);
}
function PX(x){return padL+x/SITE*SZ;}
function PY(y){return padT+(SITE-y)/SITE*SZ;}

// ---------- offscreen heat layers ----------
function lerpStops(stops,t){
  if(t<=stops[0][0])return stops[0][1];
  for(let i=1;i<stops.length;i++){
    if(t<=stops[i][0]){const a=stops[i-1],b=stops[i],f=(t-a[0])/(b[0]-a[0]);
      return [0,1,2,3].map(function(k){return a[1][k]+(b[1][k]-a[1][k])*f;});}
  }
  return stops[stops.length-1][1];
}
const PLUME_STOPS=[[0,[14,23,38,0]],[0.2,[59,15,112,150]],[0.45,[140,41,129,200]],[0.7,[222,73,104,225]],[0.88,[254,159,109,240]],[1,[252,253,191,255]]];
const GLOW_STOPS=[[0,[251,115,22,0]],[0.2,[204,76,13,64]],[0.5,[250,115,22,153]],[0.8,[255,173,64,224]],[1,[255,245,191,255]]];
const INFO_STOPS=[[0,[14,23,38,0]],[0.25,[29,78,216,120]],[0.55,[34,211,238,170]],[0.8,[251,191,36,200]],[1,[255,247,214,235]]];
const plumeCv=document.createElement("canvas"), postHalo=document.createElement("canvas"), postCore=document.createElement("canvas"), infoCv=document.createElement("canvas");
const PN=200, GN=60, IG=19;
plumeCv.width=PN; plumeCv.height=PN; postHalo.width=GN; postHalo.height=GN; postCore.width=GN; postCore.height=GN; infoCv.width=IG; infoCv.height=IG;
function buildPlume(){
  const C=new Float64Array(PN*PN), c2=plumeCv.getContext("2d"), img=c2.createImageData(PN,PN);
  const lmin=Math.log10(0.03), lmax=Math.log10(3);
  for(let j=0;j<PN;j++){for(let i=0;i<PN;i++){
    C[j*PN+i]=plume((i+0.5)/PN*SITE,SITE-(j+0.5)/PN*SITE,S.src.x,S.src.y,S.q,S.u,S.dir);
  }}
  for(let j=0;j<PN;j++){for(let i=0;i<PN;i++){
    const k=j*PN+i, c=C[k]; let col=[0,0,0,0];
    if(c>0){const t=clamp((Math.log10(c)-lmin)/(lmax-lmin),0,1); col=lerpStops(PLUME_STOPS,t);}
    if(c>=S.thr){
      const nb=[i>0?C[k-1]:0,i<PN-1?C[k+1]:0,j>0?C[k-PN]:0,j<PN-1?C[k+PN]:0];
      if(nb.some(function(v){return v<S.thr;})) col=[244,63,94,255];
    }
    img.data[k*4]=col[0];img.data[k*4+1]=col[1];img.data[k*4+2]=col[2];img.data[k*4+3]=col[3];
  }}
  c2.putImageData(img,0,0);
}
function blur(a,sig){
  const r=Math.ceil(3*sig),k=[];let sum=0;
  for(let i=-r;i<=r;i++){const v=Math.exp(-0.5*(i/sig)*(i/sig));k.push(v);sum+=v;}
  for(let i=0;i<k.length;i++)k[i]/=sum;
  const t=new Float64Array(a.length),o=new Float64Array(a.length);
  for(let y=0;y<GN;y++)for(let x=0;x<GN;x++){let s=0;for(let d=-r;d<=r;d++){const xx=x+d;if(xx>=0&&xx<GN)s+=a[y*GN+xx]*k[d+r];}t[y*GN+x]=s;}
  for(let y=0;y<GN;y++)for(let x=0;x<GN;x++){let s=0;for(let d=-r;d<=r;d++){const yy=y+d;if(yy>=0&&yy<GN)s+=t[yy*GN+x]*k[d+r];}o[y*GN+x]=s;}
  return o;
}
function paintGlow(canvas,arr,scale){
  const c2=canvas.getContext("2d"), img=c2.createImageData(GN,GN);
  let m=0; for(let i=0;i<arr.length;i++)if(arr[i]>m)m=arr[i];
  for(let k=0;k<arr.length;k++){
    const t=m>0?arr[k]/m:0; const col=t<0.05?[0,0,0,0]:lerpStops(GLOW_STOPS,t);
    img.data[k*4]=col[0];img.data[k*4+1]=col[1];img.data[k*4+2]=col[2];img.data[k*4+3]=col[3]*scale;
  }
  c2.putImageData(img,0,0);
}
function buildPosterior(){
  const dens=new Float64Array(GN*GN), r=S.res;
  for(let i=0;i<r.w.length;i++){
    const gx=Math.min(GN-1,Math.floor(r.px[i]/SITE*GN)), gy=Math.min(GN-1,Math.floor(r.py[i]/SITE*GN));
    dens[(GN-1-gy)*GN+gx]+=r.w[i];
  }
  const diffuse=r.ess>0.5*S.n;
  const halo=blur(dens,diffuse?6:3.2), core=blur(dens,diffuse?3.2:1.4);
  let pk=0; for(let i=0;i<core.length;i++)if(core[i]>pk)pk=core[i];
  const info=clamp((pk*GN*GN-1.5)/4,0.08,1);
  paintGlow(postHalo,halo,0.45*info);
  paintGlow(postCore,core,info);
}
function buildInfo(){
  const c2=infoCv.getContext("2d"), img=c2.createImageData(IG,IG);
  if(S.sug&&S.mob.on){
    const G=S.sug.G, mx=Math.sqrt(S.sug.max)||1;
    for(let gy=0;gy<G;gy++)for(let gx=0;gx<G;gx++){
      const v=S.sug.sc[gy*G+gx], row=G-1-gy, k=row*G+gx;
      const col=v<0?[0,0,0,0]:lerpStops(INFO_STOPS,Math.sqrt(v)/mx);
      img.data[k*4]=col[0];img.data[k*4+1]=col[1];img.data[k*4+2]=col[2];img.data[k*4+3]=col[3];
    }
  }
  c2.putImageData(img,0,0);
}

// ---------- sensors / inference ----------
function allSensors(){
  const a=S.sensors.map(function(s,i){return {x:s.x,y:s.y,off:s.off,name:s.name,z:S.z[i],kind:"fixed"};});
  if(S.mob.on){
    a.push({x:S.mob.x,y:S.mob.y,off:MOFF,name:"M",z:S.mob.zm,kind:"mobile"});
    S.mob.trail.forEach(function(t,i){a.push({x:t.x,y:t.y,off:MOFF,name:"M"+(i+1),z:t.z,kind:"trail"});});
  }
  return a;
}
function levelOf(r){return r>=S.thr?2:(r>=0.5*S.thr?1:0);}
function detectEvents(){
  const R=S.res;
  S.all.forEach(function(s,i){
    if(s.kind==="trail")return;
    const r=S.readings[i], lv=levelOf(r), p=S.prevLv[s.name];
    if(p!==undefined&&p!==lv)logEv(lv===2?"red":(lv===1?"amber":"green"),s.name+": "+LN[p]+" → "+LN[lv]+" ("+r.toFixed(2)+")");
    S.prevLv[s.name]=lv;
  });
  const pred=Math.max.apply(null,S.readings)>=S.thr;
  if(S.prevPred===null)logEv("blue","Twin online · "+S.n+" particles");
  else if(pred!==S.prevPred)logEv(pred?"red":"green",pred?("LEAK PREDICTED · source ≈ ("+R.x.toFixed(1)+", "+R.y.toFixed(1)+") m"):"Leak prediction cleared");
  S.prevPred=pred;
  if(S.lastEst&&!S.sim.on&&Math.hypot(R.x-S.lastEst.x,R.y-S.lastEst.y)>6){logEv("blue","Estimate moved to ("+R.x.toFixed(1)+", "+R.y.toFixed(1)+") m");S.lastEst={x:R.x,y:R.y};}
  if(!S.lastEst)S.lastEst={x:R.x,y:R.y};
}
function recompute(){
  S.all=allSensors();
  S.readings=S.all.map(function(sn){
    const e=plume(sn.x,sn.y,S.src.x,S.src.y,S.q,S.u,S.dir)+sn.off;
    return Math.max(e+S.noise*sn.z,0);
  });
  S.obsU=clamp(S.u+S.uSd*S.zWu,0.5,12); S.obsD=mod360(S.dir+S.dSd*S.zWd);
  const t0=performance.now();
  S.res=runPF({sensors:S.all,readings:S.readings,obsU:S.obsU,obsD:S.obsD,uSd:S.uSd,dSd:S.dSd,noise:S.noise,n:S.n,seed:CFG.seed+1});
  S.latency=performance.now()-t0;
  let cf=0;for(let i=0;i<S.res.w.length;i++){if(Math.hypot(S.res.px[i]-S.res.x,S.res.py[i]-S.res.y)<12)cf+=S.res.w[i];}
  S.conf=cf;
  S.sug=S.mob.on?suggestPoint(S.res,S.noise,S.all):null;
  detectEvents();
  buildPlume(); buildPosterior(); buildInfo(); updateReadout(); draw(); drawVane();
}
let pending=false;
function schedule(){if(pending)return;pending=true;requestAnimationFrame(function(){pending=false;recompute();});}

// ---------- drawing ----------
function arrowHead(c,x,y,ang,sz){
  c.beginPath();c.moveTo(x,y);c.lineTo(x-sz*Math.cos(ang-0.45),y-sz*Math.sin(ang-0.45));
  c.lineTo(x-sz*Math.cos(ang+0.45),y-sz*Math.sin(ang+0.45));c.closePath();c.fill();
}
function rayToEdge(x,y,bearingDeg){
  const a=bearingDeg*Math.PI/180, dx=Math.sin(a), dy=Math.cos(a); let t=1e9;
  if(dx>1e-9)t=Math.min(t,(SITE-x)/dx); if(dx<-1e-9)t=Math.min(t,(0-x)/dx);
  if(dy>1e-9)t=Math.min(t,(SITE-y)/dy); if(dy<-1e-9)t=Math.min(t,(0-y)/dy);
  return [x+dx*t,y+dy*t];
}
function star(c,x,y,R,r){c.beginPath();for(let i=0;i<10;i++){const a=-Math.PI/2+i*Math.PI/5,rad=i%2?r:R;c.lineTo(x+rad*Math.cos(a),y+rad*Math.sin(a));}c.closePath();}
function levelColor(r){return r>=S.thr?RED:(r>=0.5*S.thr?AMBER:CYAN);}
function tri(c,x,y,s){c.beginPath();c.moveTo(x,y-s);c.lineTo(x+s*0.95,y+s*0.8);c.lineTo(x-s*0.95,y+s*0.8);c.closePath();}
let mouse=null, drag=null;

function draw(){
  const c=ctx, R=S.res; if(!R)return;
  c.clearRect(0,0,cw,ch); c.fillStyle="#0b1220"; c.fillRect(0,0,cw,ch);
  c.fillStyle=BG; c.fillRect(padL,padT,SZ,SZ);
  c.lineWidth=1;
  for(let v=0;v<=100;v+=10){
    c.strokeStyle=(v%20===0)?"#1f2d46":"#15223a";
    c.beginPath();c.moveTo(PX(v),padT);c.lineTo(PX(v),padT+SZ);c.stroke();
    c.beginPath();c.moveTo(padL,PY(v));c.lineTo(padL+SZ,PY(v));c.stroke();
  }
  c.save(); c.beginPath(); c.rect(padL,padT,SZ,SZ); c.clip();
  c.imageSmoothingEnabled=true; c.imageSmoothingQuality="high";
  if($("L_plume").checked){c.globalAlpha=0.9;c.drawImage(plumeCv,padL,padT,SZ,SZ);c.globalAlpha=1;}
  if($("L_info").checked&&S.mob.on){c.globalAlpha=0.55;c.drawImage(infoCv,PX(2.5),PY(97.5),SZ*0.95,SZ*0.95);c.globalAlpha=1;}
  if($("L_post").checked){c.drawImage(postHalo,padL,padT,SZ,SZ);c.drawImage(postCore,padL,padT,SZ,SZ);}
  const toward=mod360(S.dir+180), ar=toward*Math.PI/180;
  c.strokeStyle="rgba(56,189,248,.20)"; c.fillStyle="rgba(56,189,248,.20)"; c.lineWidth=1.2;
  for(let gx=10;gx<=90;gx+=16)for(let gy=10;gy<=90;gy+=16){
    const x0=PX(gx),y0=PY(gy),L=11,dx=Math.sin(ar)*L,dy=-Math.cos(ar)*L;
    c.beginPath();c.moveTo(x0-dx/2,y0-dy/2);c.lineTo(x0+dx/2,y0+dy/2);c.stroke();
    arrowHead(c,x0+dx/2,y0+dy/2,Math.atan2(dy,dx),5);
  }
  if($("L_box").checked){
    const bx=PX(R.ci.x[0]),bw=PX(R.ci.x[1])-bx,by=PY(R.ci.y[1]),bh=PY(R.ci.y[0])-by;
    c.fillStyle="rgba(52,211,153,.05)";c.fillRect(bx,by,bw,bh);
    c.setLineDash([6,5]);c.strokeStyle=GREEN;c.lineWidth=1.3;c.strokeRect(bx,by,bw,bh);c.setLineDash([]);
  }
  if($("L_axis").checked){
    const e1=rayToEdge(S.src.x,S.src.y,toward);
    c.setLineDash([7,6]);c.strokeStyle="rgba(244,63,94,.75)";c.lineWidth=1.6;
    c.beginPath();c.moveTo(PX(S.src.x),PY(S.src.y));c.lineTo(PX(e1[0]),PY(e1[1]));c.stroke();
    const et=mod360(R.dir+180), e2=rayToEdge(R.x,R.y,et);
    c.strokeStyle="rgba(52,211,153,.95)";c.lineWidth=2.2;
    c.beginPath();c.moveTo(PX(R.x),PY(R.y));c.lineTo(PX(e2[0]),PY(e2[1]));c.stroke();c.setLineDash([]);
    const mx=(PX(R.x)+PX(e2[0]))/2,my=(PY(R.y)+PY(e2[1]))/2, ang=Math.atan2(PY(e2[1])-PY(R.y),PX(e2[0])-PX(R.x));
    c.fillStyle=GREEN;arrowHead(c,mx+Math.cos(ang)*8,my+Math.sin(ang)*8,ang,11);
  }
  if($("L_cloud").checked){
    c.fillStyle="rgba(226,232,240,.4)";
    const step=Math.max(1,Math.floor(R.px.length/700));
    for(let i=0;i<R.px.length;i+=step){if(R.w[i]*R.px.length<0.3)continue;c.fillRect(PX(R.px[i])-1,PY(R.py[i])-1,2,2);}
  }
  // mobile trail + route + suggested point
  if(S.mob.on){
    const pts=S.mob.trail.map(function(t){return [t.x,t.y];}); pts.push([S.mob.x,S.mob.y]);
    if(pts.length>1){c.strokeStyle="rgba(251,191,36,.85)";c.lineWidth=1.8;c.beginPath();pts.forEach(function(p,i){if(i===0)c.moveTo(PX(p[0]),PY(p[1]));else c.lineTo(PX(p[0]),PY(p[1]));});c.stroke();}
    if(S.mob.tx!==null){c.setLineDash([5,5]);c.strokeStyle="rgba(251,191,36,.95)";c.lineWidth=1.6;c.beginPath();c.moveTo(PX(S.mob.x),PY(S.mob.y));c.lineTo(PX(S.mob.tx),PY(S.mob.ty));c.stroke();c.setLineDash([]);}
    if(S.sug){
      const sx=PX(S.sug.best.x),sy=PY(S.sug.best.y);
      c.fillStyle=AMBER;c.strokeStyle="#0b1220";c.lineWidth=1.5;c.beginPath();c.moveTo(sx,sy-9);c.lineTo(sx+8,sy);c.lineTo(sx,sy+9);c.lineTo(sx-8,sy);c.closePath();c.fill();c.stroke();
      c.font="700 9px Inter,sans-serif";c.textAlign="center";c.textBaseline="bottom";c.fillStyle=AMBER;c.fillText("NEXT SAMPLE",sx,sy-11);c.textAlign="left";
    }
  }
  // sensors (fixed + live mobile + trail dots)
  for(let i=0;i<S.all.length;i++){
    const sn=S.all[i],r=S.readings[i],x=PX(sn.x),y=PY(sn.y);
    if(sn.kind==="trail"){
      c.fillStyle=levelColor(r);c.strokeStyle="#0b1220";c.lineWidth=1.2;c.beginPath();c.arc(x,y,5.5,0,7);c.fill();c.stroke();
      c.font="700 9px 'JetBrains Mono',monospace";c.fillStyle="#fde68a";c.textAlign="left";c.textBaseline="middle";c.fillText(sn.name+" "+r.toFixed(2),x+8,y+10);
      continue;
    }
    const col=levelColor(r);
    c.fillStyle=col;c.globalAlpha=0.12;c.beginPath();c.arc(x,y,24,0,7);c.fill();c.globalAlpha=0.2;c.beginPath();c.arc(x,y,14,0,7);c.fill();c.globalAlpha=1;
    c.strokeStyle=col;c.globalAlpha=0.75;c.lineWidth=1.2;c.beginPath();c.arc(x,y,9+Math.min(r/Math.max(S.thr,1e-6),2)*14,0,7);c.stroke();c.globalAlpha=1;
    c.fillStyle=col;c.strokeStyle=sn.kind==="mobile"?AMBER:"#fff";c.lineWidth=1.8;
    if(sn.kind==="mobile"){tri(c,x,y,10);c.fill();c.stroke();}else{c.fillRect(x-6,y-6,12,12);c.strokeRect(x-6,y-6,12,12);}
    const lab=sn.name+"  "+r.toFixed(2);c.font="700 11px 'JetBrains Mono',monospace";const tw=c.measureText(lab).width;
    const lx=clamp(x-tw/2-5,padL+2,padL+SZ-tw-12), ly=y-36;
    c.fillStyle="rgba(11,18,32,.88)";c.strokeStyle=sn.kind==="mobile"?AMBER:col;c.lineWidth=1;c.beginPath();c.roundRect?c.roundRect(lx,ly,tw+10,18,5):c.rect(lx,ly,tw+10,18);c.fill();c.stroke();
    c.fillStyle="#fff";c.textBaseline="middle";c.textAlign="left";c.fillText(lab,lx+5,ly+9);
  }
  // estimated source
  const ex=PX(R.x),ey=PY(R.y);
  c.strokeStyle="rgba(52,211,153,.18)";c.lineWidth=1;
  c.beginPath();c.moveTo(ex,padT);c.lineTo(ex,padT+SZ);c.moveTo(padL,ey);c.lineTo(padL+SZ,ey);c.stroke();
  c.strokeStyle="#0b1220";c.lineWidth=7;c.beginPath();c.moveTo(ex-9,ey-9);c.lineTo(ex+9,ey+9);c.moveTo(ex+9,ey-9);c.lineTo(ex-9,ey+9);c.stroke();
  c.strokeStyle=GREEN;c.lineWidth=4;c.beginPath();c.moveTo(ex-9,ey-9);c.lineTo(ex+9,ey+9);c.moveTo(ex+9,ey-9);c.lineTo(ex-9,ey+9);c.stroke();
  // true source (draggable)
  const sx=PX(S.src.x),sy=PY(S.src.y);
  c.fillStyle=RED;c.globalAlpha=0.15;c.beginPath();c.arc(sx,sy,26,0,7);c.fill();c.globalAlpha=1;
  star(c,sx,sy,15,6.5);c.fillStyle=RED;c.fill();c.strokeStyle="#fff";c.lineWidth=1.6;c.stroke();
  c.font="700 10px Inter,sans-serif";c.fillStyle="#fecdd3";c.textAlign="center";c.textBaseline="top";
  c.fillText("LEAK · drag me",sx,sy+19);c.textAlign="left";
  c.restore();
  c.strokeStyle="#2a3b57";c.lineWidth=1.4;c.strokeRect(padL,padT,SZ,SZ);
  c.fillStyle="#64748b";c.font="500 10px 'JetBrains Mono',monospace";
  c.textAlign="center";c.textBaseline="top";for(let v=0;v<=100;v+=20)c.fillText(String(v),PX(v),padT+SZ+5);
  c.textAlign="right";c.textBaseline="middle";for(let v=0;v<=100;v+=20)c.fillText(String(v),padL-6,PY(v));
  c.fillStyle="#94a3b8";c.font="600 10px Inter,sans-serif";c.textAlign="center";c.textBaseline="top";
  c.fillText("X / East (m)",padL+SZ/2,padT+SZ+22);
  c.save();c.translate(12,padT+SZ/2);c.rotate(-Math.PI/2);c.fillText("Y / North (m)",0,0);c.restore();
  c.fillStyle="#94a3b8";c.strokeStyle="#94a3b8";c.lineWidth=1.3;
  c.beginPath();c.moveTo(padL+SZ-22,padT+44);c.lineTo(padL+SZ-22,padT+22);c.stroke();arrowHead(c,padL+SZ-22,padT+20,-Math.PI/2,8);
  c.font="700 11px Inter,sans-serif";c.textAlign="center";c.textBaseline="top";c.fillText("N",padL+SZ-22,padT+47);
  if(S.sim.on){c.fillStyle="rgba(244,63,94,.9)";c.font="800 10px Inter,sans-serif";c.textAlign="left";c.textBaseline="top";c.fillText("● SIMULATION RUNNING  "+S.sim.speed+"×",padL+8,padT+8);}
  if(mouse&&mouse.inside){
    const mx=mouse.mx,my=mouse.my;
    c.strokeStyle="rgba(226,232,240,.45)";c.setLineDash([4,4]);c.lineWidth=1;
    c.beginPath();c.moveTo(mx,padT);c.lineTo(mx,padT+SZ);c.moveTo(padL,my);c.lineTo(padL+SZ,my);c.stroke();c.setLineDash([]);
    c.font="700 10px 'JetBrains Mono',monospace";
    const xt=mouse.x.toFixed(2), yt=mouse.y.toFixed(2);
    let w1=c.measureText(xt).width+10;
    c.fillStyle=CYAN;c.fillRect(clamp(mx-w1/2,padL,padL+SZ-w1),padT+SZ+1,w1,15);
    c.fillStyle="#04111f";c.textAlign="center";c.textBaseline="middle";c.fillText(xt,clamp(mx,padL+w1/2,padL+SZ-w1/2),padT+SZ+9);
    let w2=c.measureText(yt).width+10;
    c.fillStyle=CYAN;c.fillRect(padL-w2-1,clamp(my-8,padT,padT+SZ-16),w2,16);
    c.fillStyle="#04111f";c.textAlign="right";c.fillText(yt,padL-6,clamp(my,padT+8,padT+SZ-8));
    const conc=plume(mouse.x,mouse.y,S.src.x,S.src.y,S.q,S.u,S.dir);
    const dEst=Math.hypot(mouse.x-R.x,mouse.y-R.y);
    const lines=["X "+xt+" m","Y "+yt+" m","Conc "+conc.toFixed(3),"to est ✕ "+dEst.toFixed(1)+" m"];
    c.font="600 11px 'JetBrains Mono',monospace";
    let tw=0;lines.forEach(function(t){tw=Math.max(tw,c.measureText(t).width);});
    const bw=tw+16,bh=lines.length*16+10;
    let tx=mx+16,ty=my+16; if(tx+bw>padL+SZ)tx=mx-16-bw; if(ty+bh>padT+SZ)ty=my-16-bh;
    c.fillStyle="rgba(8,14,26,.92)";c.strokeStyle="#38bdf8";c.lineWidth=1;c.beginPath();
    if(c.roundRect)c.roundRect(tx,ty,bw,bh,7);else c.rect(tx,ty,bw,bh);c.fill();c.stroke();
    c.textAlign="left";c.textBaseline="middle";
    lines.forEach(function(t,i){c.fillStyle=i<2?"#e0f2fe":(i===2?"#fde68a":"#a7f3d0");c.fillText(t,tx+8,ty+13+i*16);});
  }
}

// ---------- wind vane ----------
function cardinal(d){const n=["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"];return n[Math.floor(mod360(d)/22.5+0.5)%16];}
function drawVane(){
  const c=vctx,R=S.res,cx=105,cy=105,rad=78; if(!R)return;
  c.clearRect(0,0,210,210);
  const g=c.createRadialGradient(cx,cy,5,cx,cy,rad+14);g.addColorStop(0,"#13243f");g.addColorStop(1,"#0a1220");
  c.fillStyle=g;c.beginPath();c.arc(cx,cy,rad+14,0,7);c.fill();c.strokeStyle="#28405f";c.lineWidth=1.5;c.stroke();
  c.strokeStyle="#1f3354";c.lineWidth=1;[1,0.66,0.33].forEach(function(f){c.beginPath();c.arc(cx,cy,rad*f,0,7);c.stroke();});
  for(let d=0;d<360;d+=10){
    const a=d*Math.PI/180,len=d%90===0?10:(d%30===0?6:3);
    c.strokeStyle=d%90===0?"#7dd3fc":"#3b5378";c.beginPath();
    c.moveTo(cx+rad*Math.sin(a),cy-rad*Math.cos(a));c.lineTo(cx+(rad-len)*Math.sin(a),cy-(rad-len)*Math.cos(a));c.stroke();
  }
  c.font="700 11px 'JetBrains Mono',monospace";c.textAlign="center";c.textBaseline="middle";
  [["N",0],["E",90],["S",180],["W",270]].forEach(function(p){const a=p[1]*Math.PI/180;c.fillStyle=p[0]==="N"?"#fda4af":"#9fb0c8";c.fillText(p[0],cx+(rad+9)*Math.sin(a),cy-(rad+9)*Math.cos(a));});
  function arrow(fromDeg,speed,col,w,dash){
    const toward=mod360(fromDeg+180)*Math.PI/180, L=Math.min(rad*0.92,rad*0.3+rad*0.07*speed);
    const sxp=cx-Math.sin(toward)*L/2, syp=cy+Math.cos(toward)*L/2, exp=cx+Math.sin(toward)*L/2, eyp=cy-Math.cos(toward)*L/2;
    c.strokeStyle=col;c.fillStyle=col;c.lineWidth=w;c.lineCap="round";c.setLineDash(dash||[]);
    c.beginPath();c.moveTo(sxp,syp);c.lineTo(exp,eyp);c.stroke();c.setLineDash([]);
    arrowHead(c,exp,eyp,Math.atan2(eyp-syp,exp-sxp),9);
  }
  const lo=mod360(R.ci.th[0]+180),span=mod360(R.ci.th[1]-R.ci.th[0]);
  if(span>0.5&&span<359){
    const a0=(lo-90)*Math.PI/180,a1=(lo+span-90)*Math.PI/180;
    c.fillStyle="rgba(52,211,153,.16)";c.beginPath();c.moveTo(cx,cy);c.arc(cx,cy,rad,a0,a1);c.closePath();c.fill();
  }
  arrow(S.dir,S.u,"#f8fafc",1.8,[4,4]);
  arrow(S.obsD,S.obsU,CYAN,2.4);
  arrow(R.dir,R.u,GREEN,3.2);
  const hx=cx+rad*Math.sin(S.dir*Math.PI/180),hy=cy-rad*Math.cos(S.dir*Math.PI/180);
  c.fillStyle="rgba(244,63,94,.25)";c.beginPath();c.arc(hx,hy,13,0,7);c.fill();
  c.fillStyle=RED;c.strokeStyle="#fff";c.lineWidth=1.8;c.beginPath();c.arc(hx,hy,7,0,7);c.fill();c.stroke();
  c.fillStyle="#0b1220";c.strokeStyle=CYAN;c.lineWidth=1.5;c.beginPath();c.arc(cx,cy,4.5,0,7);c.fill();c.stroke();
}

// ---------- readout / notice / alerts ----------
function setPill(cls,txt){return "<span class='pill "+cls+"'><span class='dot'></span>"+txt+"</span>";}
function chipFor(lv){return "<span class='chip "+(lv===2?"red":(lv===1?"amber":"green"))+"'>"+LN[lv]+"</span>";}
function updateReadout(){
  const R=S.res, peak=Math.max.apply(null,S.readings);
  let pk=0;for(let i=1;i<S.readings.length;i++)if(S.readings[i]>S.readings[pk])pk=i;
  const nm=S.all[pk].name;
  const rad=Math.max((R.ci.x[1]-R.ci.x[0])/2,(R.ci.y[1]-R.ci.y[0])/2);
  let p1,p2,p3,ncls,nico,ntitle,nsub;
  if(peak>=S.thr){
    p1=setPill("red","CRITICAL LEAK DETECTED"); ncls="red"; nico="🚨"; ntitle="SENSOR LEAK PREDICTED";
    nsub="Strongest "+nm+" ("+peak.toFixed(2)+") · source ≈ ("+R.x.toFixed(1)+", "+R.y.toFixed(1)+") m ± "+rad.toFixed(0)+" m · confidence "+(S.conf*100).toFixed(0)+"% · wind FROM "+R.dir.toFixed(0)+"° "+cardinal(R.dir);
  } else if(peak>=0.5*S.thr){
    p1=setPill("amber","ELEVATED CONCENTRATION · MONITORING"); ncls="amber"; nico="⚠"; ntitle="ELEVATED CONCENTRATION · MONITORING";
    nsub=nm+" reads "+peak.toFixed(2)+" (warn ≥ "+(0.5*S.thr).toFixed(2)+", alarm ≥ "+S.thr.toFixed(2)+")";
  } else {
    p1=setPill("green","NO ALARM · ALL NODES BELOW THRESHOLD"); ncls="green"; nico="✔"; ntitle="NO LEAK PREDICTED";
    nsub="All nodes below warning level · peak "+peak.toFixed(2)+" · ESS "+R.ess.toFixed(0);
  }
  const L=S.latency;
  if(L<50)p2=setPill("green","CYBER-PHYSICAL EDGE LATENCY CALIBRATED · "+L.toFixed(0)+" ms");
  else if(L<2000)p2=setPill("amber","LATENCY "+L.toFixed(0)+" ms · ABOVE 50 ms TARGET, WITHIN 2 s BUDGET");
  else p2=setPill("red","LATENCY BUDGET EXCEEDED · "+L.toFixed(0)+" ms");
  const w=0.5*((R.ci.x[1]-R.ci.x[0])+(R.ci.y[1]-R.ci.y[0]));
  if(R.ess<15)p3=setPill("amber","LOW PARTICLE DIVERSITY · ESS "+R.ess.toFixed(0));
  else if(w<25)p3=setPill("green","POSTERIOR CONVERGED · 95% CI WIDTH "+w.toFixed(0)+" m");
  else if(w<50)p3=setPill("amber","POSTERIOR NARROWING · 95% CI WIDTH "+w.toFixed(0)+" m");
  else p3=setPill("amber","POSTERIOR DIFFUSE · 95% CI WIDTH "+w.toFixed(0)+" m");
  const nf=S.sensors.length+(S.mob.on?1+S.mob.trail.length:0);
  $("pills").innerHTML=p1+p2+p3+setPill("blue",nf+" MEASUREMENTS ASSIMILATED"+(S.mob.on?" · MOBILE ACTIVE":""))+(S.sim.on?setPill("red","SIMULATION RUNNING"):"");
  const nt=$("notice"); nt.className="notice "+ncls; $("n_ico").textContent=nico; $("n_title").textContent=ntitle; $("n_sub").textContent=nsub;
  let active=0; S.all.forEach(function(s,i){if(s.kind!=="trail"&&levelOf(S.readings[i])>0)active++;});
  if(peak>=S.thr)active++;
  const bn=$("bellN"); bn.textContent=active; bn.className="badge"+(active?"":" zero");
  const rb=$("railBadge"); rb.textContent=active; rb.style.display=active?"block":"none";
  // detection table
  function cov(v,ci){return (v>=ci[0]&&v<=ci[1])?"<span class='ok'>✓</span>":"<span class='bad'>✗</span>";}
  const dT=mod360(S.dir-R.dir+180)-180, covDir=(dT>=(mod360(R.ci.th[0]-R.dir+180)-180)&&dT<=(mod360(R.ci.th[1]-R.dir+180)-180))?"<span class='ok'>✓</span>":"<span class='bad'>✗</span>";
  let bi=0;for(let i=1;i<S.sensors.length;i++)if(S.readings[i]>S.readings[bi])bi=i;
  const baseErr=Math.hypot(S.sensors[bi].x-S.src.x,S.sensors[bi].y-S.src.y), err=Math.hypot(R.x-S.src.x,R.y-S.src.y);
  const rows=[
    ["Source X (m)",S.src.x.toFixed(1),R.x.toFixed(1),"["+R.ci.x[0].toFixed(1)+", "+R.ci.x[1].toFixed(1)+"] "+cov(S.src.x,R.ci.x)],
    ["Source Y (m)",S.src.y.toFixed(1),R.y.toFixed(1),"["+R.ci.y[0].toFixed(1)+", "+R.ci.y[1].toFixed(1)+"] "+cov(S.src.y,R.ci.y)],
    ["Release Q",S.q.toFixed(0),R.q.toFixed(1),"["+R.ci.q[0].toFixed(0)+", "+R.ci.q[1].toFixed(0)+"] "+cov(S.q,R.ci.q)],
    ["Wind FROM",S.dir.toFixed(0)+"° "+cardinal(S.dir),R.dir.toFixed(0)+"° "+cardinal(R.dir),"±"+R.ci.half.toFixed(0)+"° "+covDir],
    ["Wind speed",S.u.toFixed(1)+" m/s",R.u.toFixed(2)+" m/s","["+R.ci.u[0].toFixed(1)+", "+R.ci.u[1].toFixed(1)+"] "+cov(S.u,R.ci.u)],
    ["Spreads toward",mod360(S.dir+180).toFixed(0)+"° "+cardinal(S.dir+180),mod360(R.dir+180).toFixed(0)+"° "+cardinal(R.dir+180),""],
    ["Location error",err.toFixed(1)+" m","",""],
    ["Baseline error",baseErr.toFixed(1)+" m","strongest fixed sensor",(err<baseErr?"<span class='ok'>twin closer</span>":"<span class='bad'>baseline closer</span>")],
    ["Update / ESS",L.toFixed(1)+" ms","ESS "+R.ess.toFixed(0),""]
  ];
  $("tb").innerHTML=rows.map(function(r){return "<tr><td>"+r[0]+"</td><td>"+r[1]+"</td><td>"+r[2]+"</td><td>"+r[3]+"</td></tr>";}).join("");
  $("scn").textContent="leak ("+S.src.x.toFixed(1)+", "+S.src.y.toFixed(1)+") m · Q "+S.q.toFixed(0)+" · wind FROM "+S.dir.toFixed(0)+"° @ "+S.u.toFixed(1)+" m/s";
  // alerts panel
  $("al_sensors").innerHTML=S.all.filter(function(s){return s.kind!=="trail";}).map(function(s){
    const i=S.all.indexOf(s), r=S.readings[i];
    return "<tr><td>"+s.name+"</td><td>"+r.toFixed(2)+"</td><td>"+chipFor(levelOf(r))+"</td><td>"+Math.hypot(s.x-R.x,s.y-R.y).toFixed(0)+" m</td></tr>";
  }).join("");
  const dp=$("al_dispatch");
  if(peak>=0.5*S.thr){
    dp.className="disp "+(peak>=S.thr?"red":"amber");
    dp.innerHTML="<b>"+(peak>=S.thr?"DISPATCH · INSPECT":"WATCH")+"</b><br>Inspect zone centred ("+R.x.toFixed(0)+", "+R.y.toFixed(0)+") m, radius "+Math.max(rad,5).toFixed(0)+" m. Approach from upwind: "+cardinal(R.dir)+" ("+R.dir.toFixed(0)+"°). Confidence "+(S.conf*100).toFixed(0)+"%.";
  } else {dp.className="disp green";dp.innerHTML="<b>ALL CLEAR</b><br>No node above warning level. No dispatch needed.";}
  $("al_feed").innerHTML=S.events.slice().reverse().map(function(e){return "<div class='ev "+e.level+"'><b>"+e.t+"</b>"+e.msg+"</div>";}).join("");
  updateMobStat();
}
function updateMobStat(){
  const m=S.mob, el=$("m_stat");
  if(!m.on){el.textContent="Mobile sensor not deployed.";return;}
  el.textContent="M at ("+m.x.toFixed(1)+", "+m.y.toFixed(1)+") m · samples "+m.trail.length+"/"+m.len+
    (m.tx!==null?" · moving to ("+m.tx.toFixed(0)+", "+m.ty.toFixed(0)+")":"")+
    (S.sug?" · suggested ("+S.sug.best.x+", "+S.sug.best.y+") m":"")+(m.auto?" · AUTO":"");
}

// ---------- controls ----------
function syncSliders(){
  $("s_dir").value=Math.round(S.dir);$("o_dir").textContent=Math.round(S.dir)+"°";
  $("s_u").value=S.u;$("o_u").textContent=S.u.toFixed(1);
  $("s_dsd").value=S.dSd;$("o_dsd").textContent=S.dSd.toFixed(0)+"°";
  $("s_usd").value=S.uSd;$("o_usd").textContent=S.uSd.toFixed(1);
  $("s_q").value=S.q;$("o_q").textContent=S.q.toFixed(0);
  $("s_n").value=S.noise;$("o_n").textContent=S.noise.toFixed(2);
  $("s_t").value=S.thr;$("o_t").textContent=S.thr.toFixed(1);
  $("s_p").value=String(S.n);
  $("s_lx").value=S.src.x;$("o_lx").textContent=S.src.x.toFixed(1);
  $("s_ly").value=S.src.y;$("o_ly").textContent=S.src.y.toFixed(1);
  $("m_x").value=S.mob.x;$("o_mx").textContent=S.mob.x.toFixed(1);
  $("m_y").value=S.mob.y;$("o_my").textContent=S.mob.y.toFixed(1);
  $("m_speed").value=S.mob.speed;$("o_msp").textContent=S.mob.speed+" m/s";
  $("m_len").value=S.mob.len;$("o_mlen").textContent=String(S.mob.len);
  $("m_on").checked=S.mob.on;
  $("b_auto").textContent="Auto-guide: "+(S.mob.auto?"ON":"OFF"); $("b_auto").className=S.mob.auto?"on":"";
  [$("b_sim"),$("b_simS")].forEach(function(b){b.textContent=S.sim.on?"⏸ Pause":"▶ Simulate";b.className=S.sim.on?"on":"";});
}
function bind(id,key,label,fmt){
  $(id).addEventListener("input",function(e){S[key]=parseFloat(e.target.value);syncSliders();schedule();});
  $(id).addEventListener("change",function(){logEv("blue",label+" → "+fmt(S[key]));schedule();});
}
bind("s_dir","dir","Wind FROM",function(v){return v.toFixed(0)+"°";});
bind("s_u","u","Wind speed",function(v){return v.toFixed(1)+" m/s";});
bind("s_dsd","dSd","Wind-dir telemetry σ",function(v){return v.toFixed(0)+"°";});
bind("s_usd","uSd","Wind-speed telemetry σ",function(v){return v.toFixed(1)+" m/s";});
bind("s_q","q","Release rate Q",function(v){return v.toFixed(0);});
bind("s_n","noise","Sensor noise",function(v){return v.toFixed(2);});
bind("s_t","thr","Alarm threshold",function(v){return v.toFixed(1);});
$("s_lx").addEventListener("input",function(e){S.src.x=parseFloat(e.target.value);syncSliders();schedule();});
$("s_ly").addEventListener("input",function(e){S.src.y=parseFloat(e.target.value);syncSliders();schedule();});
["s_lx","s_ly"].forEach(function(id){$(id).addEventListener("change",function(){logEv("blue","Leak moved to ("+S.src.x.toFixed(1)+", "+S.src.y.toFixed(1)+") m");});});
$("b_center").addEventListener("click",function(){S.src.x=50;S.src.y=50;logEv("blue","Leak centred at (50, 50) m");syncSliders();schedule();});
$("s_p").addEventListener("change",function(e){S.n=parseInt(e.target.value,10);logEv("blue","Particles → "+S.n);schedule();});
$("s_sp").addEventListener("change",function(e){S.sim.speed=parseFloat(e.target.value);schedule();});
$("c_move").addEventListener("change",function(e){S.sim.move=e.target.checked;logEv("blue","Moving leak "+(S.sim.move?"enabled":"disabled"));});
$("c_veer").addEventListener("change",function(e){S.sim.veer=e.target.checked;logEv("blue","Wind veer/turbulence "+(S.sim.veer?"enabled":"disabled"));});
["L_plume","L_post","L_axis","L_box","L_cloud","L_info"].forEach(function(id){$(id).addEventListener("change",function(){draw();});});
$("b_noise").addEventListener("click",function(){S.nc++;regenNoise();logEv("blue","New noise sample drawn");schedule();});
$("b_reset").addEventListener("click",function(){
  S.src={x:INIT.leak_x,y:INIT.leak_y};S.q=INIT.strength;S.u=INIT.wind_speed;S.dir=INIT.wind_from;S.noise=INIT.noise;S.thr=INIT.threshold;S.n=INIT.n_particles;
  S.uSd=INIT.wind_speed_sd;S.dSd=INIT.wind_dir_sd;
  S.sensors=INIT.sensors.map(function(s){return {x:s.x,y:s.y,off:s.off,name:s.name};});
  S.mob.trail=[];S.mob.tx=null;S.mob.ty=null;S.mob.auto=false;S.mob.x=INIT.mobile_x;S.mob.y=INIT.mobile_y;
  S.sim.on=false;S.nc=0;regenNoise();logEv("blue","Scenario reset");syncSliders();schedule();
});
// mobile controls
function addSample(){
  if(!S.mob.on||S.mob.trail.length>=MAXTRAIL)return false;
  S.mob.cnt++; const r=makeRng(CFG.seed*13+5+S.mob.cnt*17);
  S.mob.trail.push({x:S.mob.x,y:S.mob.y,z:r.n()});
  logEv("amber","Mobile sample #"+S.mob.trail.length+" at ("+S.mob.x.toFixed(1)+", "+S.mob.y.toFixed(1)+") m assimilated");
  return true;
}
$("m_on").addEventListener("change",function(e){
  S.mob.on=e.target.checked; if(!S.mob.on){S.mob.auto=false;S.mob.tx=null;}
  logEv("amber","Mobile sensor "+(S.mob.on?"deployed":"recalled")); syncSliders(); schedule();
});
$("m_x").addEventListener("input",function(e){S.mob.x=parseFloat(e.target.value);S.mob.tx=null;syncSliders();schedule();});
$("m_y").addEventListener("input",function(e){S.mob.y=parseFloat(e.target.value);S.mob.tx=null;syncSliders();schedule();});
$("m_speed").addEventListener("input",function(e){S.mob.speed=parseFloat(e.target.value);syncSliders();});
$("m_len").addEventListener("input",function(e){S.mob.len=parseInt(e.target.value,10);syncSliders();updateMobStat();});
$("b_take").addEventListener("click",function(){if(!S.mob.on){$("m_on").checked=true;S.mob.on=true;}addSample();syncSliders();schedule();});
$("b_go").addEventListener("click",function(){
  if(!S.mob.on){S.mob.on=true;syncSliders();schedule();return;}
  if(S.sug){S.mob.tx=S.sug.best.x;S.mob.ty=S.sug.best.y;logEv("amber","Mobile sensor dispatched to ("+S.mob.tx+", "+S.mob.ty+") m");schedule();}
});
$("b_auto").addEventListener("click",function(){
  if(!S.mob.on){S.mob.on=true;}
  S.mob.auto=!S.mob.auto; if(S.mob.auto&&S.mob.trail.length>=S.mob.len){S.mob.trail=[];}
  logEv("amber","Auto-guide "+(S.mob.auto?"ON · active sensing":"OFF")); syncSliders(); schedule();
});
$("b_clear").addEventListener("click",function(){S.mob.trail=[];S.mob.tx=null;S.mob.auto=false;logEv("amber","Mobile trail cleared");syncSliders();schedule();});

// ---------- simulation + mobile motion ----------
function toggleSim(){
  S.sim.on=!S.sim.on; logEv(S.sim.on?"red":"blue",S.sim.on?"Simulation started · wind veer / turbulence live":"Simulation paused");
  syncSliders(); schedule();
}
$("b_sim").addEventListener("click",toggleSim);
$("b_simS").addEventListener("click",toggleSim);
function simStep(){
  const r=S.sim.rng, sp=S.sim.speed, dt=0.12*sp; S.sim.tick++;
  if(S.sim.veer){
    S.dir=mod360(S.dir+(Math.sin(S.sim.tick*0.05)*6+r.n()*5)*dt);
    S.u=clamp(S.u+r.n()*0.35*dt,0.5,10);
  }
  if(S.sim.move){
    S.src.x+=S.sim.vx*dt; S.src.y+=S.sim.vy*dt;
    if(S.src.x<8||S.src.x>92){S.sim.vx*=-1;S.src.x=clamp(S.src.x,8,92);}
    if(S.src.y<8||S.src.y>92){S.sim.vy*=-1;S.src.y=clamp(S.src.y,8,92);}
  }
  if(S.sim.tick%4===0){S.nc++;regenNoise();}
  syncSliders();
}
function mobStep(){
  const m=S.mob; if(!m.on)return false;
  if(m.auto&&m.tx===null){
    if(m.trail.length>=m.len){m.auto=false;logEv("green","Mobile mission complete · "+m.trail.length+" samples");syncSliders();return true;}
    if(S.sug){m.tx=S.sug.best.x;m.ty=S.sug.best.y;logEv("amber","Auto-guide → next sample at ("+m.tx+", "+m.ty+") m");}
  }
  if(m.tx===null)return false;
  const step=m.speed*0.12*S.sim.speed, dx=m.tx-m.x, dy=m.ty-m.y, d=Math.hypot(dx,dy);
  if(d<=step){m.x=m.tx;m.y=m.ty;m.tx=null;m.ty=null;addSample();syncSliders();}
  else{m.x+=dx/d*step;m.y+=dy/d*step;syncSliders();}
  return true;
}
setInterval(function(){
  if(drag||vdrag)return;
  let need=false;
  if(S.sim.on){simStep();need=true;}
  if(mobStep())need=true;
  if(need)schedule();
},120);

// ---------- panels / fullscreen ----------
function openPanel(name){
  const dr=$("drawer");
  if(S.panel===name){S.panel=null;dr.classList.remove("open");}
  else{S.panel=name;dr.classList.add("open");}
  ["settings","source","mobile","alerts"].forEach(function(p){$("pn_"+p).classList.toggle("on",S.panel===p);});
  document.querySelectorAll(".rb").forEach(function(b){b.classList.toggle("on",b.getAttribute("data-p")===S.panel);});
  setTimeout(function(){layout();draw();drawVane();},210);
}
document.querySelectorAll(".rb").forEach(function(b){b.addEventListener("click",function(){openPanel(b.getAttribute("data-p"));});});
$("b_bell").addEventListener("click",function(){if(S.panel!=="alerts")openPanel("alerts");});
$("b_fs").addEventListener("click",function(){
  const el=$("app");
  try{
    if(!document.fullscreenElement){
      const p=(el.requestFullscreen||el.webkitRequestFullscreen).call(el);
      if(p&&p.catch)p.catch(function(){logEv("amber","Full screen blocked by the browser · use 'Expanded view' in the Streamlit tab instead");updateReadout();});
    } else {document.exitFullscreen();}
  }catch(e){logEv("amber","Full screen not available here · use 'Expanded view' in the Streamlit tab instead");updateReadout();}
});
document.addEventListener("fullscreenchange",function(){
  const fs=!!document.fullscreenElement;
  $("app").classList.toggle("fs",fs); $("b_fs").textContent=fs?"✕ Exit full screen":"⛶ Full screen";
  setTimeout(function(){layout();draw();drawVane();},80);
});
window.addEventListener("resize",function(){layout();draw();});

// ---------- pointer interaction: map ----------
function toData(ev){
  const r=cv.getBoundingClientRect(),mx=ev.clientX-r.left,my=ev.clientY-r.top;
  const x=(mx-padL)/SZ*SITE,y=SITE-(my-padT)/SZ*SITE;
  return {mx:mx,my:my,x:x,y:y,inside:x>=0&&x<=SITE&&y>=0&&y<=SITE};
}
function hit(p){
  if(Math.hypot(p.mx-PX(S.src.x),p.my-PY(S.src.y))<=20)return {type:"src"};
  if(S.mob.on&&Math.hypot(p.mx-PX(S.mob.x),p.my-PY(S.mob.y))<=16)return {type:"mob"};
  for(let i=0;i<S.sensors.length;i++)if(Math.hypot(p.mx-PX(S.sensors[i].x),p.my-PY(S.sensors[i].y))<=14)return {type:"sensor",i:i};
  return null;
}
cv.addEventListener("pointerdown",function(ev){
  const p=toData(ev),h=hit(p);
  if(h){drag=h;cv.setPointerCapture(ev.pointerId);cv.style.cursor="grabbing";ev.preventDefault();}
});
cv.addEventListener("pointermove",function(ev){
  const p=toData(ev);mouse=p;
  if(drag){
    const x=clamp(p.x,0,SITE),y=clamp(p.y,0,SITE);
    if(drag.type==="src"){S.src.x=x;S.src.y=y;}
    else if(drag.type==="mob"){S.mob.x=x;S.mob.y=y;S.mob.tx=null;}
    else{S.sensors[drag.i].x=x;S.sensors[drag.i].y=y;}
    syncSliders();schedule();
  } else {
    cv.style.cursor=hit(p)?"grab":(p.inside?"crosshair":"default");
    draw();
  }
  $("cursorTxt").textContent=p.inside?("CURSOR  X "+p.x.toFixed(2)+"  Y "+p.y.toFixed(2)):"CURSOR — outside map";
});
function endDrag(ev){
  if(drag){
    if(drag.type==="src")logEv("blue","Leak dragged to ("+S.src.x.toFixed(1)+", "+S.src.y.toFixed(1)+") m");
    else if(drag.type==="mob")logEv("amber","Mobile sensor placed at ("+S.mob.x.toFixed(1)+", "+S.mob.y.toFixed(1)+") m");
    else logEv("blue","Sensor "+S.sensors[drag.i].name+" moved to ("+S.sensors[drag.i].x.toFixed(1)+", "+S.sensors[drag.i].y.toFixed(1)+") m");
    drag=null;try{cv.releasePointerCapture(ev.pointerId);}catch(e){}cv.style.cursor="crosshair";schedule();
  }
}
cv.addEventListener("pointerup",endDrag);
cv.addEventListener("pointercancel",endDrag);
cv.addEventListener("pointerleave",function(){if(!drag){mouse=null;draw();$("cursorTxt").textContent="CURSOR — move over the map";}});

// ---------- pointer interaction: wind vane ----------
var vdrag=false;
function vaneSet(ev){
  const r=vcv.getBoundingClientRect(),dx=ev.clientX-r.left-105,dy=ev.clientY-r.top-105;
  if(Math.hypot(dx,dy)<6)return;
  S.dir=mod360(Math.atan2(dx,-dy)*180/Math.PI);syncSliders();schedule();
}
vcv.addEventListener("pointerdown",function(ev){vdrag=true;vcv.setPointerCapture(ev.pointerId);vaneSet(ev);ev.preventDefault();});
vcv.addEventListener("pointermove",function(ev){if(vdrag)vaneSet(ev);});
vcv.addEventListener("pointerup",function(){if(vdrag)logEv("blue","Wind vane set to FROM "+S.dir.toFixed(0)+"° "+cardinal(S.dir));vdrag=false;});
vcv.addEventListener("pointercancel",function(){vdrag=false;});
vcv.style.cursor="grab";

if(window.ResizeObserver){new ResizeObserver(function(){layout();if(S.res){draw();drawVane();}}).observe(stage);}
layout();syncSliders();recompute();
if(CFG.open_panel)openPanel(CFG.open_panel);
})();
</script>
</body>
</html>
'''


def build_interactive_html(cfg: dict) -> str:
    return INTERACTIVE_HTML.replace("__CONFIG__", json.dumps(cfg))
