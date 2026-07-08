async function approve(btn){
 btn.disabled=true;
 btn.textContent="Starting…";
 try{
  const r=await fetch("/api/work/approve",{
method:"POST",   headers:{
"Content-Type":"application/json"}
,   body:JSON.stringify({
uri:btn.dataset.uri}
)}
);
  const d=await r.json();
  if(d.ok){
btn.classList.add("done");
   btn.textContent="Approved — running (see Runs panel)";
   btn.title=d.message||"";
loadRuns();
}
  else{
btn.classList.add("err");
btn.disabled=false;
   btn.textContent=(d.error||"Failed")+" — retry";
}
 }
catch(e){
btn.classList.add("err");
btn.disabled=false;
btn.textContent="Error — retry";
}
}
const openRuns=new Set();
function fmtWhen(ts){
if(!ts)return"";
const s=Math.max(0,(Date.now()/1000)-ts);
 if(s<90)return Math.round(s)+"s ago";
if(s<5400)return Math.round(s/60)+"m ago";
 return new Date(ts*1000).toLocaleString();
}
function runStatus(r){
if(r.running)return["st-running","running"];
 if(r.exit===0)return["st-ok","exit 0"];
 if(r.exit===null||r.exit===undefined)return["st-done","finished"];
 return["st-fail","exit "+r.exit];
}
function runCard(r){
const card=document.createElement("div");
card.className="run-card";
 if(openRuns.has(r.id)||r.running)card.classList.add("open");
 const head=document.createElement("div");
head.className="run-head";
 const st=document.createElement("span");
const[c,t]=runStatus(r);
st.className="st "+c;
st.textContent=t;
 const uri=document.createElement("span");
uri.className="uri";
uri.textContent=r.uri||r.id;
 const when=document.createElement("span");
when.className="run-when";
when.textContent=fmtWhen(r.started);
 head.append(st,uri,when);
card.append(head);
 if(r.label){
const l=document.createElement("div");
l.className="run-label";
l.textContent=r.label;
card.append(l);
}
 const log=document.createElement("pre");
log.className="run-log";
 log.textContent=r.tail||"(no output yet)";
card.append(log);
 head.onclick=()=>{
card.classList.toggle("open");
  card.classList.contains("open")?openRuns.add(r.id):openRuns.delete(r.id);
  if(card.classList.contains("open"))log.scrollTop=log.scrollHeight;
}
;
 return card;
}
async function loadRuns(){
try{
 const r=await fetch("/api/work/runs");
const d=await r.json();
const runs=d.runs||[];
 const sec=document.getElementById("runs");
sec.hidden=runs.length===0;
 document.getElementById("runcount").textContent=runs.length;
 const list=document.getElementById("runlist");
list.replaceChildren(...runs.map(runCard));
 list.querySelectorAll(".run-card.open .run-log").forEach(l=>l.scrollTop=l.scrollHeight);
 if(runs.some(x=>x.running))clearTimeout(loadRuns._t),loadRuns._t=setTimeout(loadRuns,2500);
 else clearTimeout(loadRuns._t),loadRuns._t=setTimeout(loadRuns,10000);
}
catch(e){
clearTimeout(loadRuns._t);
loadRuns._t=setTimeout(loadRuns,10000);
}
}
loadRuns();
async function loadStatus(){
try{
 const r=await fetch("/api/work/status");
const d=await r.json();
 const box=document.getElementById("continuity");
const c=d.continuity||"?";
 box.className="cont "+(c==="OK"?"cont-ok":c==="STOPPED"?"cont-stopped":"cont-risk");
 const k=d.koru||{
}
;
const t=d.tickets||{
}
;
 document.getElementById("contbig").textContent="CONTINUITY: "+c;
 const seen=k.last_seen_seconds;
 document.getElementById("contsub").textContent=  (k.running?"koru RUNNING":"koru STOPPED")  +(seen!=null?" · heartbeat "+seen+"s ago":"")  +" · open "+(t.open||0)+" · in-progress "+(t.in_progress||0)+" · blocked "+(t.blocked||0)+" · done "+(t.done||0)  +(d.current?(" · now "+d.current.id):(d.next&&d.next[0]?(" · next "+d.next[0].id):""));
 document.getElementById("contaction").textContent=d.suggested_action?("→ "+d.suggested_action):"";
 clearTimeout(loadStatus._t);
loadStatus._t=setTimeout(loadStatus,5000);
}
catch(e){
clearTimeout(loadStatus._t);
loadStatus._t=setTimeout(loadStatus,10000);
}
}
loadStatus();
window._grantKeys=new Set();
window._grantTickets=new Set();
window._ledgerPath="";
function scrollToGrants(){
document.getElementById("grants")?.scrollIntoView({
behavior:"smooth",block:"start"}
);
}
function scrollToQueue(){
document.getElementById("queue")?.scrollIntoView({
behavior:"smooth",block:"start"}
);
}
function refreshAll(){
loadStatus();
loadQueue();
loadUnblocks();
loadRuns();
loadOps();
loadUriLog();
 loadWatchdog();
loadGaps();
loadLoop();
loadKoruLog();
loadActive();
loadDigitalTwin();
}
async function copyLedgerPath(){
const st=document.getElementById("grants-status");
 const p=window._ledgerPath||document.getElementById("grants-path").textContent.replace(/^plik:\s*/,"");
 if(!p){
st.textContent="brak ścieżki ledgera";
return;
}
 const ok=await copyToClipboard(p);
st.textContent=ok?("skopiowano: "+p):("ścieżka: "+p);
}
function ticketGrantHit(t){
if(!t||!window._grantKeys)return null;
 if(window._grantTickets.has(t.id))return t.id;
 for(const lab of (t.labels||[])){
const l=String(lab).toLowerCase();
  if(window._grantKeys.has(l))return l;
  if(l.startsWith("waiting:")){
const g="wait-gate:waiting_"+l.split(":")[1];
if(window._grantKeys.has(g))return g;
}
}
 return null;
}
function grantRow(g,revokeKind){
const row=document.createElement("div");
row.className="grant-item";
 const key=document.createElement("span");
key.className="grant-key";
  key.textContent=g.key||g.ticket||"?";
 const meta=document.createElement("span");
meta.className="grant-meta";
  meta.textContent=(g.ticket?("z "+g.ticket+" · "):"")+(g.action?("akcja "+g.action+" · "):"")   +(g.note||g.by||"");
 const when=document.createElement("span");
when.className="grant-when";
  when.textContent=g.unblocked_at?fmtWhen(g.unblocked_at):"";
 const rev=document.createElement("button");
rev.className="grant-rev";
rev.textContent="Cofnij";
  rev.onclick=()=>revokeGrant(g.key||g.ticket,revokeKind);
 row.append(key,meta,when,rev);
return row;
}
async function revokeGrant(key,kind){
const st=document.getElementById("grants-status");
 if(!confirm("Cofnąć trwałe odblokowanie "+key+"?"))return;
 st.textContent="cofam "+key+"…";
 try{
const r=await fetch("/api/work/unblocks",{
method:"POST",  headers:{
"Content-Type":"application/json"}
,  body:JSON.stringify({
action:kind||"revoke",key}
)}
);
  const d=await r.json();
st.textContent=d.ok?("cofnięto "+(d.revoked||key)):("błąd: "+(d.error||"?"));
  loadUnblocks();
loadQueue();
 }
catch(e){
st.textContent="błąd: "+e;
}
}
async function loadUnblocks(andQueue){
try{
 const d=await(await fetch("/api/work/unblocks")).json();
 window._ledgerPath=d.ledger||"";
 document.getElementById("grants-path").textContent=d.ledger?("plik: "+d.ledger):"";
 window._grantKeys=new Set((d.types||[]).map(g=>(g.key||"").trim()).filter(Boolean));
 window._grantTickets=new Set((d.tickets||[]).map(g=>(g.ticket||g.key||"").trim()).filter(Boolean));
 const types=document.getElementById("grants-types");
types.textContent="";
 const tks=(d.types||[]);
const legacy=(d.tickets||[]);
 const cnt=document.getElementById("grants-count");
 cnt.textContent=(tks.length?(tks.length+" typów"):"")+(legacy.length?((tks.length?" · ":"")+legacy.length+" ticketów"):"")  ||"brak grantów";
 if(!tks.length){
const e=document.createElement("div");
e.className="grants-empty";
  const msg=document.createElement("span");
  msg.textContent="Brak grantów per typ — Odblokuj ticket w kolejce (zapisze też klucze waiting/action).";
  const b=document.createElement("button");
b.className="grant-btn";
b.textContent="▶ Idź do kolejki";
  b.onclick=scrollToQueue;
e.append(msg,b);
types.append(e);
}
 else types.append(...tks.map(g=>grantRow(g,"revoke")));
 const tw=document.getElementById("grants-tickets-wrap");
const tl=document.getElementById("grants-tickets");
 tl.textContent="";
 tw.hidden=!legacy.length;
 if(legacy.length)tl.append(...legacy.map(g=>grantRow(g,"revoke-ticket")));
 if(andQueue)loadQueue();
 clearTimeout(loadUnblocks._t);
loadUnblocks._t=setTimeout(()=>loadUnblocks(false),15000);
}
catch(e){
clearTimeout(loadUnblocks._t);
loadUnblocks._t=setTimeout(()=>loadUnblocks(false),20000);
}
}
loadUnblocks(true);
async function loadDigitalTwin(){
try{
 const r=await fetch("/api/work/persons");
const d=await r.json();
 const dt=d.persons||[];
 const el=document.getElementById("dt-persons");
el.textContent="";
 if(!dt.length){
el.textContent="brak definicji digital persons";
return;
}
 dt.forEach(p=>{
  const row=document.createElement("div");
row.style.margin="2px 0";
  const b=document.createElement("span");
b.className="grantchip";
b.style.background="rgba(164,147,214,.3)";
b.textContent=(p.type==="human"?"👤":"🤖")+p.id;
  const n=document.createElement("span");
n.textContent=" "+(p.name||"")+" ";
  const c=document.createElement("span");
c.style.color="var(--dim)";
c.textContent="["+ (p.competencies||[]).slice(0,3).join(", ") + (p.competencies&&p.competencies.length>3?"…":"") +"] ";
  const g=document.createElement("span");
g.style.fontSize="9px";
g.textContent="grants: "+(p.grants||[]).slice(0,2).join(", ");
  row.append(b,n,c,g);
  if(p.model){
const m=document.createElement("span");
m.className="llmtag";
m.textContent=p.model;
row.append(m);
}
  el.append(row);
 }
);
}
catch(e){
}
}
loadDigitalTwin();
async function continueKoru(btn){
const s=document.getElementById("korubtnstatus");
 btn.disabled=true;
s.textContent="uruchamiam koru…";
 try{
const r=await fetch("/api/work/koru",{
method:"POST",  headers:{
"Content-Type":"application/json"}
,body:JSON.stringify({
lane:"queue"}
)}
);
  const d=await r.json();
  s.textContent=d.ok?(d.already_running?"koru już działa":"koru uruchomiony — pętla wznowiona"):("błąd: "+(d.error||"?"));
  loadStatus();
 }
catch(e){
s.textContent="błąd: "+e;
}
btn.disabled=false;
}
function fmtTime(v){
if(!v)return"";
let ms;
 if(typeof v==="number")ms=v<1e12?v*1000:v;
 else{
const d=Date.parse(v);
if(isNaN(d))return"";
ms=d;
}
 const s=Math.max(0,(Date.now()-ms)/1000);
 if(s<90)return Math.round(s)+"s temu";
if(s<5400)return Math.round(s/60)+"m temu";
 if(s<172800)return Math.round(s/3600)+"h temu";
return new Date(ms).toLocaleString();
}
function mkTkBtn(label,fn,primary){
const b=document.createElement("button");
 b.className="tkbtn"+(primary?" primary":"");
b.textContent=label;
b.onclick=fn;
return b;
}
async function ticketAct(id,action,note){
const s=document.getElementById("dbgstatus");
 if(s)s.textContent=id+": "+(action||"notatka")+"…";
 try{
const r=await fetch("/api/work/ticket",{
method:"POST",   headers:{
"Content-Type":"application/json"}
,body:JSON.stringify({
id,action,note:note||""}
)}
);
  const d=await r.json();
  if(s)s.textContent=d.ok?(id+" · "+(action||"notatka")+" ✓ ("+new Date().toLocaleTimeString()+")")    :(id+" błąd: "+(d.error||"?"));
  loadQueue();
loadStatus();
loadUnblocks();
 }
catch(e){
if(s)s.textContent=id+" błąd: "+e;
}
}
async function archiveAllDone(){
const s=document.getElementById("dbgstatus");
 if(s)s.textContent="Archiwizuję zakończone...";
 try{
  const r=await fetch("/api/work/queue?include_done=true");
 const d=await r.json();
  const dones = (d.tickets||[]).filter(t => t.status==="done");
  for(const t of dones){
    await fetch("/api/work/ticket",{
method:"POST", headers:{
"Content-Type":"application/json"}
, body:JSON.stringify({
id:t.id, action:"archive"}
)}
);
  }
  if(s)s.textContent="Zarchiwizowano "+dones.length+" ticketów.";
 loadQueue();
 }
catch(e){
if(s)s.textContent="Błąd archiwizacji: "+e;
}
}
function ticketNoteInline(id,act){
act.innerHTML="";
 const i=document.createElement("input");
i.className="tk-note";
i.placeholder="notatka…";
 const ok=mkTkBtn("Zapisz",()=>{
if(i.value.trim())ticketAct(id,"note",i.value.trim());
}
);
 i.addEventListener("keydown",e=>{
if(e.key==="Enter"&&i.value.trim())ticketAct(id,"note",i.value.trim());
}
);
 act.append(i,ok);
i.focus();
}
function renderTicket(t){
const wrap=document.createElement("div");
wrap.className="tk-wrap";
 const row=document.createElement("div");
row.className="tk";
 const id=document.createElement("span");
id.className="tid";
id.textContent=t.id||"";
 const stt=document.createElement("span");
  const auto = t.autonomy || "";
  let stClass = "tst-"+(t.status||"open");
  let stText = (t.status||"").replace("_"," ");
  if (auto === "granted_blocked") {
 stClass = "tst-blocked tst-granted";
 stText = "blocked (granted)";
 }
  else if (auto === "granted_open" || auto === "granted") {
 stClass = "tst-open tst-granted";
 }
  stt.className = "tst " + stClass;
  stt.textContent = stText;
 const main=document.createElement("div");
main.className="tk-main";
  const nm=document.createElement("span");
nm.className="tk-name";
nm.textContent=t.name||"";
main.append(nm);
  (t.llm||[]).forEach(x=>{
const l=document.createElement("span");
l.className="llmtag";
l.textContent=x;
main.append(l);
}
);
  if(t.llm_model){
const lm=document.createElement("span");
lm.className="llmtag";
lm.textContent="🤖 "+t.llm_model;
main.append(lm);
}
  if(t.node){
const nd=document.createElement("span");
nd.className="nodechip";
nd.textContent=t.node;
main.append(nd);
}
  if(t.owner){
const ow=document.createElement("span");
ow.className="nodechip";
ow.style.background="rgba(75,179,166,.2)";
ow.textContent=(t.owner.type==="human"?"👤 ":"🤖 ")+(t.owner.name||t.owner.id);
main.append(ow);
}
  if(t.assigned_person && !t.owner){
const ap=document.createElement("span");
ap.className="nodechip";
ap.textContent="👤 "+t.assigned_person;
main.append(ap);
}
  if(t.schedule){
const sc=document.createElement("span");
sc.className="schedchip";
sc.textContent=t.schedule;
main.append(sc);
}
  // server now provides t.grant + t.autonomy (added for long-term viz of autonomous work)  let gh = (t.grant && (t.grant.key || t.grant)) || ticketGrantHit(t);
  if(gh){
const gc=document.createElement("span");
gc.className="grantchip";
   gc.textContent="✓ grant: "+gh;
gc.title="Trwałe odblokowanie (per typ lub ticket) — autonomia nie będzie ponownie prosić człowieka o ten sam przypadek";
main.append(gc);
}
  if (t.autonomy && t.autonomy.includes("granted")) {
    const ap=document.createElement("span");
ap.className="grantchip";
 ap.style.background="var(--done-bg)";
ap.style.color="var(--done)";
    ap.textContent = "auto";
 ap.title = t.autonomy + (t.autonomy_note?": "+t.autonomy_note:"");
 main.append(ap);
 }
 const meta=document.createElement("span");
meta.className="tsrc";
  const wh=document.createElement("span");
wh.className="tk-when";
wh.textContent=t.updated?("zmiana "+fmtTime(t.updated)):"";
  meta.append(wh,document.createTextNode(t.source?(" · "+t.source):""));
 const act=document.createElement("span");
act.className="tk-act";
  const bl=(t.status==="blocked"||t.status==="waiting_input");
  const wip=(t.status==="in_progress"||t.status==="claimed");
  if(bl){
const gl = (t.grant && (t.grant.key || t.grant)) || ticketGrantHit(t);
   const btnLabel = gl ? "Otwórz (force — grant)" : "Odblokuj ▶ (+typ)";
   act.append(mkTkBtn(btnLabel,()=>ticketAct(t.id,"unblock"),!gl));
   if(gl) act.append(mkTkBtn("Granty",scrollToGrants));
 }
  if(t.status==="open")act.append(mkTkBtn("▶ Start",()=>ticketAct(t.id,"start"),true));
  if(wip){
act.append(mkTkBtn("Gotowe",()=>ticketAct(t.id,"done")));
   act.append(mkTkBtn("Wstrzymaj",()=>ticketAct(t.id,"block")));
}
  if(bl||wip||t.status==="open")act.append(mkTkBtn("Notatka",()=>ticketNoteInline(t.id,act)));
  if(t.editable)act.append(mkTkBtn("Edytuj",()=>openTkModal(t,true)));
  if(t.status!=="done"&&t.status!=="closed"&&t.status!=="cancelled")   act.append(mkTkBtn("Zamknij",()=>ticketAct(t.id,"close")));
  if(t.status==="done") {
   const isArch = (t.sprint || "") === "archive";
   const lbl = isArch ? "Przywróć" : "Archiwizuj";
   const actName = isArch ? "unarchive" : "archive";
   act.append(mkTkBtn(lbl,()=> {
 if(confirm(lbl + " ticket "+t.id+"?")) ticketAct(t.id, actName);
 }
 ));
 }
  act.append(mkTkBtn("Usuń",()=>{
ticketAct(t.id,"delete");
}
));
 row.append(id,stt,main,meta,act);
wrap.append(row);
 if(t.procs&&t.procs.length){
const sub=document.createElement("div");
sub.className="tk-sub";
  const names=t.procs.slice(0,3).map(p=>p.label||p.kind||p.detail||"proces");
  const b=document.createElement("b");
b.textContent="procesy: ";
sub.append(b,document.createTextNode(   names.join("  │  ")+(t.procs_total>3?"  …  ("+t.procs_total+")":"")));
  sub.title="Kliknij: pełna lista procesów";
sub.onclick=()=>openTkModal(t,t.editable);
wrap.append(sub);
}
 return wrap;
}
function closeTkModal(){
document.getElementById("tkmodal").classList.remove("open");
}
async function openTkModal(t,editable){
const body=document.getElementById("tkmodal-body");
 body.textContent="";
const h=document.createElement("h3");
h.textContent=(t.id||"")+" — ładuję…";
body.append(h);
 document.getElementById("tkmodal").classList.add("open");
 try{
const d=await(await fetch("/api/work/ticket/detail?id="+encodeURIComponent(t.id))).json();
  renderTkModal(t,d,editable);
}
catch(e){
h.textContent=(t.id||"")+" — błąd: "+e;
}
}
function _pf(label,key,val,ta){
const w=document.createElement("div");
 const l=document.createElement("label");
l.textContent=label;
 const i=document.createElement(ta?"textarea":"input");
i.value=val||"";
i.dataset.k=key;
if(ta)i.rows=2;
 w.append(l,i);
return w;
}
function renderTkModal(t,d,editable){
const body=document.getElementById("tkmodal-body");
body.textContent="";
 const h=document.createElement("h3");
h.textContent=(t.id||"")+" — procesy ("+(d.process_total||0)+")";
body.append(h);
 const pl=document.createElement("div");
pl.className="proc-list";
 (d.processes||[]).forEach(p=>{
const r=document.createElement("div");
r.className="proc-row";
  const a=document.createElement("span");
a.className="pt";
a.textContent=p.time||"";
  const b=document.createElement("span");
b.className="pl";
b.textContent=p.label||p.kind||"";
  const c=document.createElement("span");
c.className="pd";
c.textContent=p.detail||"";
  r.append(a,b,c);
pl.append(r);
}
);
 if(!(d.processes||[]).length){
const e=document.createElement("div");
e.className="proc-row";
  e.textContent="(brak zarejestrowanych procesów dla tego ticketu)";
pl.append(e);
}
 body.append(pl);
 if(!editable){
const n=document.createElement("div");
n.className="edit-hint";
  n.textContent="Ticket zakończony — edycja niedostępna.";
body.append(n);
return;
}
 const hint=document.createElement("div");
hint.className="edit-hint";
  hint.textContent="Edycja (puste pole = bez zmian):";
body.append(hint);
 const g=document.createElement("div");
g.className="edit-grid";
  g.append(_pf("Nazwa ticketu","name",t.name),_pf("Opis (zastąpi istniejący)","description","",true),   _pf("LLM (tagi, po przecinku)","llm",(d.llm&&d.llm.length?d.llm:t.llm||[]).join(", ")),   _pf("LLM Model","llm_model",d.llm_model||t.llm_model||""),   _pf("Node / maszyna","node",d.node||t.node||""),   _pf("Owner (digital person id lub human)","owner", (t.owner&&t.owner.id)||t.assigned_person||""),   _pf("Assigned Person","assigned_person",t.assigned_person||""),   _pf("Harmonogram (np. codziennie 08:00 / cron)","schedule",d.schedule||t.schedule||""),   _pf("Allow URI (po przecinku)","allow",(d.allow||[]).join(", "),true),   _pf("Deny URI (po przecinku)","deny",(d.deny||[]).join(", "),true));
 body.append(g);
 const btn=document.createElement("button");
btn.className="edit-save";
btn.textContent="Zapisz zmiany";
 const st=document.createElement("span");
st.className="modal-status";
 btn.onclick=async()=>{
const payload={
id:t.id}
;
  g.querySelectorAll("[data-k]").forEach(i=>{
const v=i.value.trim();
   if(["llm","allow","deny","node","schedule"].includes(i.dataset.k)||v)payload[i.dataset.k]=v;
}
);
  st.textContent="zapisuję…";
btn.disabled=true;
  try{
const r=await(await fetch("/api/work/ticket/edit",{
method:"POST",    headers:{
"Content-Type":"application/json"}
,body:JSON.stringify(payload)}
)).json();
   st.textContent=r.ok?("zapisano ✓ ("+new Date().toLocaleTimeString()+")"):("błąd: "+(r.error||"?"));
   if(r.ok)loadQueue();
}
catch(e){
st.textContent="błąd: "+e;
}
btn.disabled=false;
}
;
 const bar=document.createElement("div");
bar.append(btn,st);
body.append(bar);
}
async function loadQueue(){
try{
 const showArchived = document.getElementById("showArchived") ? document.getElementById("showArchived").checked : false;
 const url = showArchived ? "/api/work/queue?include_done=true&sprint=archive" : "/api/work/queue";
 const r=await fetch(url);
const d=await r.json();
 const sec=document.getElementById("queue");
sec.hidden=false;
 const k=d.koru||{
}
;
 const st=document.getElementById("korustate");
 st.className=k.running?"koru-live":"koru-dead";
 st.textContent=k.running?"● RUNNING (loop nie stoi)":"○ stopped";
 document.getElementById("qcount").textContent=d.total||0;
 const granted = (d.tickets||[]).filter(t => (t.autonomy||"").includes("granted")).length;
 const grantedEl = document.getElementById("qgranted");
 if (grantedEl) grantedEl.textContent = granted ? " · " + granted + " granted (autonomous)" : "";
 document.getElementById("korulast").textContent=k.last_activity||"";
 const list=document.getElementById("ticketlist");
 list.replaceChildren(...(d.tickets||[]).map(t=>renderTicket(t)));
 loadDigitalTwin();
 clearTimeout(loadQueue._t);
loadQueue._t=setTimeout(loadQueue,5000);
}
catch(e){
clearTimeout(loadQueue._t);
loadQueue._t=setTimeout(loadQueue,10000);
}
}
loadQueue();
async function loadActive(){
try{
 const r=await fetch("/api/work/active");
const d=await r.json();
 const actives=d.active||[];
 document.getElementById("activecount").textContent=actives.length;
 const sec=document.getElementById("active");
 sec.hidden=actives.length===0;
 const list=document.getElementById("activelist");
list.textContent="";
 actives.forEach(a=>{
  const row=document.createElement("div");
row.className="tk";
  const b=document.createElement("span");
b.className="tst";
  b.textContent=a.badge||"▶";
  if(a.badge_label==="pause")b.style.background="#fde047";
  else if(a.badge_label==="stop")b.style.background="#fda4af";
  else b.style.background="var(--run-bg)";
  const id=document.createElement("span");
id.className="tid";
id.textContent=a.id;
  const nm=document.createElement("span");
nm.textContent=a.name||"";
  const wk=document.createElement("span");
wk.className="tsrc";
wk.textContent=" · "+(a.worker||"");
  row.append(b,id,nm,wk);
  if(a.expires_in!=null){
const ex=document.createElement("span");
ex.className="tk-when";
ex.textContent=" "+a.expires_in+"s";
row.append(ex);
}
  list.append(row);
 }
);
 clearTimeout(loadActive._t);
loadActive._t=setTimeout(loadActive,3000);
}
catch(e){
clearTimeout(loadActive._t);
loadActive._t=setTimeout(loadActive,8000);
}
}
loadActive();
async function copyToClipboard(text){
 if(navigator.clipboard&&window.isSecureContext){
  try{
await navigator.clipboard.writeText(text);
return true;
}
catch(e){
}
}
 const ta=document.createElement("textarea");
ta.value=text;
 ta.style.position="fixed";
ta.style.left="-9999px";
ta.setAttribute("readonly","");
 document.body.appendChild(ta);
ta.select();
 let ok=false;
try{
ok=document.execCommand("copy");
}
catch(e){
ok=false;
}
 ta.remove();
return ok;
}
async function copyState(btn){
const st=document.getElementById("dbgstatus");
 btn.disabled=true;
st.textContent="pobieram…";
 try{
const r=await fetch("/api/work/debug");
const d=await r.json();
  const text=JSON.stringify(d.state||d,null,1);
  const ok=await copyToClipboard(text);
  st.textContent=ok?("stan w schowku ("+Math.round(text.length/1024)+" kB JSON)")   :("skopiuj ręcznie — schowek niedostępny po HTTP");
 }
catch(e){
st.textContent="błąd: "+e;
}
btn.disabled=false;
}
async function makeSnapshot(btn){
const st=document.getElementById("dbgstatus");
 btn.disabled=true;
st.textContent="zapisuję zrzut…";
 try{
const r=await fetch("/api/work/debug/snapshot",{
method:"POST",  headers:{
"Content-Type":"application/json"}
,body:"{}"}
);
const d=await r.json();
  st.textContent=d.ok?("zrzut: "+d.path+" ("+Math.round((d.bytes||0)/1024)+" kB) — debug://host/snapshot/query/list"):("błąd: "+(d.error||"?"));
 }
catch(e){
st.textContent="błąd: "+e;
}
btn.disabled=false;
}
async function copyEndpoint(url,key,btn){
const old=btn.textContent;
btn.disabled=true;
btn.textContent="…";
 try{
const d=await(await fetch(url)).json();
const obj=(key&&d[key]!==undefined)?d[key]:d;
  const ok=await copyToClipboard(JSON.stringify(obj,null,1));
btn.textContent=ok?"✓ JSON":"ręcznie";
 }
catch(e){
btn.textContent="błąd";
}
 setTimeout(()=>{
btn.textContent=old;
btn.disabled=false;
}
,1900);
}
async function copyPanel(btn){
const old=btn.textContent;
btn.disabled=true;
btn.textContent="pobieram…";
 try{
const[st,q,ops,runs,ulog]=await Promise.all([   fetch("/api/work/status").then(r=>r.json()),   fetch("/api/work/queue").then(r=>r.json()),   fetch("/api/work/ops").then(r=>r.json()),   fetch("/api/work/runs").then(r=>r.json()),   fetch("/api/work/uri-log").then(r=>r.json())]);
  const panel={
continuity:st,queue:q,ops:ops.ops,runs:runs.runs,uriLog:ulog.events}
;
  const text=JSON.stringify(panel,null,1);
const ok=await copyToClipboard(text);
  btn.textContent=ok?("✓ panel w schowku ("+Math.round(text.length/1024)+" kB)"):"skopiuj ręcznie";
 }
catch(e){
btn.textContent="błąd: "+e;
}
 setTimeout(()=>{
btn.textContent=old;
btn.disabled=false;
}
,2600);
}
function opRow(o){
const row=document.createElement("div");
row.className="op";
 const main=document.createElement("div");
 const t=document.createElement("div");
t.className="otitle";
t.textContent=o.title||o.uri||o.id;
main.append(t);
 if(o.uri){
const u=document.createElement("div");
u.className="ouri";
u.textContent=o.uri;
main.append(u);
}
 if(o.desc){
const d=document.createElement("div");
d.className="odesc";
d.textContent=o.desc;
main.append(d);
}
 if(o.cmd){
const c=document.createElement("div");
c.className="ocmd";
c.textContent="$ "+o.cmd;
main.append(c);
}
 if(o.llm){
const lm=document.createElement("div");
lm.className="op-llm";
lm.textContent=o.llm;
main.append(lm);
}
 const side=document.createElement("div");
side.className="op-btns";
 if(o.status==="pending"){
  const ok=document.createElement("button");
ok.className="op-confirm";
ok.textContent="Zatwierdź ▶";
  ok.onclick=()=>opAction(o.id,"confirm",row);
  const no=document.createElement("button");
no.className="op-reject";
no.textContent="Odrzuć";
  no.onclick=()=>opAction(o.id,"reject",row);
side.append(ok,no);
 }
else{
const st=document.createElement("span");
st.className="op-st ost-"+o.status;
  st.textContent=o.status;
side.append(st);
}
 const tm=document.createElement("div");
tm.className="op-time";
  tm.textContent=(o.status==="pending"?"dodano ":"zmiana ")+fmtTime(o.updated||o.created);
  side.append(tm);
 row.append(main,side);
return row;
}
async function opAction(id,action,row){
row.querySelectorAll("button").forEach(b=>b.disabled=true);
 try{
await fetch("/api/work/ops/"+action,{
method:"POST",  headers:{
"Content-Type":"application/json"}
,body:JSON.stringify({
id}
)}
);
  loadOps();
if(action==="confirm")loadRuns();
 }
catch(e){
row.querySelectorAll("button").forEach(b=>b.disabled=false);
}
}
async function loadOps(){
try{
 const r=await fetch("/api/work/ops");
const d=await r.json();
const ops=d.ops||[];
 const sec=document.getElementById("ops");
sec.hidden=ops.length===0;
 document.getElementById("opcount").textContent=ops.filter(o=>o.status==="pending").length;
 document.getElementById("oplist").replaceChildren(...ops.map(opRow));
 clearTimeout(loadOps._t);
loadOps._t=setTimeout(loadOps,4000);
}
catch(e){
clearTimeout(loadOps._t);
loadOps._t=setTimeout(loadOps,10000);
}
}
loadOps();
function ustClass(s){
if(s==="degraded")return"ust-degraded";
 if(s==="fail"||s==="failed"||s==="error")return"ust-fail";
 if(s==="ok"||s==="known-good"||s==="done")return"ust-ok";
return"";
}
async function loadUriLog(){
try{
 const r=await fetch("/api/work/uri-log");
const d=await r.json();
const ev=d.events||[];
 const sec=document.getElementById("urilog");
sec.hidden=ev.length===0;
 document.getElementById("ulogcount").textContent=ev.length;
 document.getElementById("uloglist").replaceChildren(...ev.map(e=>{
  const row=document.createElement("div");
row.className="ue";
  const dot=document.createElement("span");
dot.className="ust "+ustClass(e.status);
  const cat=document.createElement("span");
cat.className="ucat";
cat.textContent=e.category||"";
  const box=document.createElement("div");
  const u=document.createElement("div");
u.className="uuri";
u.textContent=e.uri||"";
box.append(u);
  if(e.narration){
const n=document.createElement("div");
n.className="unar";
n.textContent=e.narration;
box.append(n);
}
  row.append(dot,cat,box);
return row;
}
));
 clearTimeout(loadUriLog._t);
loadUriLog._t=setTimeout(loadUriLog,3500);
}
catch(e){
clearTimeout(loadUriLog._t);
loadUriLog._t=setTimeout(loadUriLog,10000);
}
}
loadUriLog();
const shout=document.getElementById("shout");
document.getElementById("shform").addEventListener("submit",async function(ev){
 ev.preventDefault();
const inp=document.getElementById("shcmd");
const cmd=inp.value.trim();
 if(!cmd)return;
shout.textContent+="["+new Date().toLocaleTimeString()+"] $ "+cmd+"\n";
 inp.value="";
shout.scrollTop=shout.scrollHeight;
 try{
const r=await fetch("/api/work/shell",{
method:"POST",  headers:{
"Content-Type":"application/json"}
,body:JSON.stringify({
cmd}
)}
);
const d=await r.json();
  if(d.ok){
shout.textContent+=(d.out||"");
   if(d.out&&!d.out.endsWith("\n"))shout.textContent+="\n";
   shout.textContent+="[exit "+d.exit+(d.truncated?" · output obcięty":"")+"]\n\n";
}
  else{
shout.textContent+="[błąd] "+(d.error||"?")+"\n\n";
}
 }
catch(e){
shout.textContent+="[błąd] "+e+"\n\n";
}
 shout.scrollTop=shout.scrollHeight;
}
);
async function loadWatchdog(){
try{
 const d=await(await fetch("/api/work/watchdog")).json();
 const box=document.getElementById("watchdog");
const stuck=(d&&d.stuck)||[];
 box.classList.toggle("on",stuck.length>0);
 const list=document.getElementById("wd-list");
list.textContent="";
 stuck.forEach(t=>{
const row=document.createElement("div");
row.className="wd-item";
  const id=document.createElement("span");
id.className="wd-id";
id.textContent=t.id;
  const mid=document.createElement("div");
   const cat=document.createElement("span");
cat.className="wd-cat";
cat.textContent=t.category;
   const rc=document.createElement("div");
rc.className="wd-rc";
    rc.textContent=t.rootcause+" → "+t.action+(t.streak?("  (streak "+t.streak+", drive_failed "+t.drive_failed+")"):"")     +(t.dead_loop?("  ⛔ OSCYLACJA "+t.cycles+"× — Odblokuj NIE pomoże, usuń rootcause"):"");
   mid.append(cat,rc);
  const acts=document.createElement("div");
acts.style.cssText="display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end";
  if(t.dead_loop){
const cb=document.createElement("button");
cb.className="wd-fix";
   cb.textContent="⛔ Zdiagnozuj ("+t.cycles+"× cykl)";
cb.onclick=()=>wdBreak(t.id,cb);
acts.append(cb);
}
  else{
const b=document.createElement("button");
b.className="wd-fix";
b.textContent="Przerwij pętlę ▸";
   b.onclick=()=>wdUnstick(t.id,b);
acts.append(b);
}
  if(t.category==="no_executor"||t.category==="idle_claim"||t.dead_loop){
   const ra=document.createElement("button");
ra.className="wd-fix";
ra.style.background="#2f8f84";
   ra.textContent="▶ Wykonaj agentem";
ra.onclick=()=>wdRunAgent(t.id,ra);
acts.append(ra);
}
  row.append(id,mid,acts);
list.append(row);
}
);
 clearTimeout(loadWatchdog._t);
loadWatchdog._t=setTimeout(loadWatchdog,8000);
}
catch(e){
clearTimeout(loadWatchdog._t);
loadWatchdog._t=setTimeout(loadWatchdog,15000);
}
}
loadWatchdog();
async function wdUnstick(id,btn){
const st=document.getElementById("wd-status");
 btn.disabled=true;
st.textContent=id+": przerywam pętlę…";
 try{
const r=await(await fetch("/api/work/watchdog",{
method:"POST",   headers:{
"Content-Type":"application/json"}
,body:JSON.stringify({
action:"unstick",id}
)}
)).json();
  if(r.ok){
st.textContent=id+" → blocked, eskalowano do operatora ✓ ("+new Date().toLocaleTimeString()+")";
   loadWatchdog();
loadQueue();
}
else{
st.textContent="błąd: "+(r.error||"?");
btn.disabled=false;
}
 }
catch(e){
st.textContent="błąd: "+e;
btn.disabled=false;
}
}
async function wdBreak(id,btn){
const st=document.getElementById("wd-status");
btn.disabled=true;
 st.textContent=id+": diagnozuję oscylację…";
 try{
const r=await(await fetch("/api/work/watchdog",{
method:"POST",   headers:{
"Content-Type":"application/json"}
,body:JSON.stringify({
action:"circuit-break",id}
)}
)).json();
  st.textContent=r.ok?(id+" → breaker otwarty, diagnoza "+(r.diagnosis||"?")+" ✓ — NIE odblokowuj bez fixu"):("błąd: "+(r.error||"?"));
  loadWatchdog();
loadQueue();
}
catch(e){
st.textContent="błąd: "+e;
btn.disabled=false;
}
}
async function wdRunAgent(id,btn){
const st=document.getElementById("wd-status");
btn.disabled=true;
 st.textContent=id+": uruchamiam agenta (claude -p)…";
 try{
const r=await(await fetch("/api/work/agents",{
method:"POST",   headers:{
"Content-Type":"application/json"}
,body:JSON.stringify({
action:"run-ticket",id}
)}
)).json();
  st.textContent=r.ok?(id+" → agent "+(r.agent||"")+" wykonuje realnie (patrz Runs) ✓"):("błąd: "+(r.error||"?"));
  loadRuns();
}
catch(e){
st.textContent="błąd: "+e;
btn.disabled=false;
}
}
async function loadGaps(){
try{
 const d=await(await fetch("/api/work/gaps")).json();
 const box=document.getElementById("gaps");
const rows=(d&&d.tickets)||[];
 box.classList.toggle("on",rows.length>0||((d.systemic||[]).length>0));
 const sys=document.getElementById("gaps-sys");
sys.textContent="";
 (d.systemic||[]).forEach(s=>{
const p=document.createElement("div");
p.className="gap-sys";
  const b=document.createElement("b");
b.textContent="• ";
p.append(b,document.createTextNode(s));
sys.append(p);
}
);
 const list=document.getElementById("gaps-list");
list.textContent="";
 rows.forEach(r=>{
const row=document.createElement("div");
row.className="gap-item";
  const id=document.createElement("span");
id.className="gap-id";
id.textContent=r.id;
  const rdy=document.createElement("span");
rdy.className="gap-rdy "+(r.ready?"yes":"no");
   rdy.textContent=r.ready?"gotowy":"luka";
  const nx=document.createElement("span");
nx.className="gap-next";
   nx.textContent=r.next_action+((r.missing&&r.missing.length)?("  ["+r.missing.join(", ")+"]"):"");
  row.append(id,rdy,nx);
list.append(row);
}
);
 clearTimeout(loadGaps._t);
loadGaps._t=setTimeout(loadGaps,12000);
}
catch(e){
clearTimeout(loadGaps._t);
loadGaps._t=setTimeout(loadGaps,20000);
}
}
loadGaps();
async function loadLoop(){
try{
 const d=await(await fetch("/api/work/loop")).json();
 const box=document.getElementById("loop");
const acts=(d&&d.actions)||[];
 box.classList.toggle("on",acts.length>0);
 const list=document.getElementById("loop-list");
list.textContent="";
 acts.forEach(a=>{
const row=document.createElement("div");
row.className="loop-item";
  const id=document.createElement("span");
id.className="gap-id";
id.textContent=a.ticket;
  const act=document.createElement("span");
act.className="loop-act "+a.risk;
act.textContent=a.action;
  const why=document.createElement("span");
why.className="loop-why";
why.textContent=a.reason;
  row.append(id,act,why);
list.append(row);
}
);
 clearTimeout(loadLoop._t);
loadLoop._t=setTimeout(loadLoop,12000);
}
catch(e){
clearTimeout(loadLoop._t);
loadLoop._t=setTimeout(loadLoop,20000);
}
}
loadLoop();
async function runLoopCycle(btn){
const st=document.getElementById("loop-st");
btn.disabled=true;
 const auto=document.getElementById("loop-auto").checked;
 st.textContent="uruchamiam cykl"+(auto?" (auto-agent — zmienia repo)":" (safe)")+"…";
 try{
const r=await(await fetch("/api/work/loop",{
method:"POST",   headers:{
"Content-Type":"application/json"}
,body:JSON.stringify({
apply:true,auto_agent:auto}
)}
)).json();
  st.textContent=r.ok?("cykl: "+(r.did||0)+"/"+(r.total||0)+" akcji zastosowanych ✓ ("+new Date().toLocaleTimeString()+")"):("błąd: "+(r.error||"?"));
  loadLoop();
loadWatchdog();
loadQueue();
loadGaps();
}
catch(e){
st.textContent="błąd: "+e;
}
btn.disabled=false;
}
let koruLines=[];
const koruTypes=new Set();
let koruCmdOnly=false,koruLoopOnly=false;
const KORU_LOOP=5;
function koruAge(s){
if(s==null)return "?";
if(s<120)return Math.round(s)+"s";
 if(s<7200)return Math.floor(s/60)+"min";
return (s/3600).toFixed(1)+"h";
}
function koruSrc(p){
return p?String(p).split("/").pop():"brak logu";
}
function renderKoruStatus(d){
const el=document.getElementById("klogstatus");
if(!el)return;
 const st=(d&&d.status)||"unavailable",ctrl=(d&&d.controller)||"brak kontrolera",src=koruSrc(d&&d.log);
 el.className="klogstatus "+st;
 if(d&&d.live)el.textContent="live · "+src;
 else if(st==="missing")el.textContent="brak logu · "+ctrl;
 else if(d&&d.stale)el.textContent="stare "+koruAge(d.source_age_seconds)+" · "+ctrl;
 else el.textContent=st+" · "+ctrl;
 el.title="source="+(d&&d.log||"")+"; mtime="+(d&&d.source_mtime_local||"")+"; server="+(d&&d.server_time||"");
}
function koruRow(l){
const r=document.createElement("div");
r.className="krow"+(l.count>=KORU_LOOP?" loop":"");
 const t=document.createElement("span");
t.className="kt";
t.textContent=l.last||l.time||"";
 const ty=document.createElement("span");
ty.className="kty kty-"+(l.type||"LOG");
ty.textContent=(l.type||"LOG").slice(0,4);
 const tx=document.createElement("span");
tx.className="ktx"+(String(l.text||"").includes("$ ")?" cmd":"");
tx.textContent=l.text||"";
 const cn=document.createElement("span");
  if(l.count>1){
cn.className="kcount";
cn.textContent="×"+l.count;
cn.title="pierwszy "+(l.first||"?")+", ostatni "+(l.last||"?");
}
 r.append(t,ty,tx,cn);
return r;
}
function renderKoruRows(){
const box=document.getElementById("kloglist");
if(!box)return;
 const atBottom=box.scrollTop+box.clientHeight>=box.scrollHeight-40;
 const rows=koruLines.filter(l=>{
  if(koruCmdOnly&&!String(l.text||"").includes("$ "))return false;
  if(koruLoopOnly&&!(l.count>=KORU_LOOP))return false;
  if(koruTypes.size&&!koruTypes.has(l.type))return false;
return true;
}
);
 box.replaceChildren(...rows.map(koruRow));
 document.getElementById("klogcount").textContent=rows.length;
 if(atBottom)box.scrollTop=box.scrollHeight;
}
function koruToggle(f,btn){
const allBtn=document.querySelector(".klf[data-f=all]");
 if(f==="all"){
koruTypes.clear();
koruCmdOnly=false;
koruLoopOnly=false;
  document.querySelectorAll(".klf").forEach(b=>b.classList.remove("on"));
btn.classList.add("on");
}
 else{
if(f==="cmd")koruCmdOnly=!koruCmdOnly;
else if(f==="loop")koruLoopOnly=!koruLoopOnly;
  else{
koruTypes.has(f)?koruTypes.delete(f):koruTypes.add(f);
}
  btn.classList.toggle("on");
if(allBtn)allBtn.classList.remove("on");
  if(!koruCmdOnly&&!koruLoopOnly&&!koruTypes.size&&allBtn)allBtn.classList.add("on");
}
 renderKoruRows();
}
async function loadKoruLog(){
try{
 const d=await(await fetch("/api/work/koru-log?tail=200")).json();
 renderKoruStatus(d);
 koruLines=(d&&d.lines)||[];
 document.getElementById("korulog").hidden=koruLines.length===0&&!((d&&d.status));
renderKoruRows();
 clearTimeout(loadKoruLog._t);
loadKoruLog._t=setTimeout(loadKoruLog,2500);
}
catch(e){
clearTimeout(loadKoruLog._t);
loadKoruLog._t=setTimeout(loadKoruLog,6000);
}
}
loadKoruLog();
async function loadCron(){
try{
 const d=await(await fetch("/api/work/cron")).json();
 const sec=document.getElementById("cron");
sec.hidden=false;
 const list=document.getElementById("cron-list");
 if(!d.ok){
document.getElementById("cron-cal").textContent="";
  list.textContent="cron:// niedostępny: "+(d.error||"zainstaluj urirun-connector-cron");
return;
}
 const cal=d.calendar||{
}
;
const ents=d.entries||[];
 document.getElementById("croncount").textContent=ents.length;
 const cc=document.getElementById("cron-cal");
cc.className="cron-cal";
cc.textContent="";
 const bd=cal.byDay||{
}
;
const days=Object.keys(bd).sort();
 if(!days.length){
const e=document.createElement("div");
e.className="cal-day";
  e.textContent="brak nadchodzących uruchomień";
cc.append(e);
}
 days.forEach(dt=>{
const col=document.createElement("div");
col.className="cal-day";
  const h=document.createElement("h4");
h.textContent=dt;
col.append(h);
  bd[dt].slice(0,8).forEach(o=>{
const r=document.createElement("div");
r.className="cal-ev";
   const t=document.createElement("span");
t.className="ct";
t.textContent=o.time+" ";
   r.append(t,document.createTextNode(o.label||""));
col.append(r);
}
);
cc.append(col);
}
);
 list.textContent="";
 ents.forEach(e=>{
const row=document.createElement("div");
row.className="cron-row";
  const s=document.createElement("span");
s.className="csch";
s.textContent=e.schedule;
  const c=document.createElement("span");
c.className="ccmd";
c.textContent=(e.label?("["+e.label+"] "):"")+e.command;
  const a=document.createElement("span");
a.className="tk-act";
  if(e.managed)a.append(mkTkBtn("Usuń",()=>cronRemove(e.id)));
  else{
const g=document.createElement("span");
g.className="tsrc";
g.textContent="systemowy";
a.append(g);
}
  row.append(s,c,a);
list.append(row);
}
);
 clearTimeout(loadCron._t);
loadCron._t=setTimeout(loadCron,15000);
}
catch(e){
clearTimeout(loadCron._t);
loadCron._t=setTimeout(loadCron,20000);
}
}
loadCron();
async function loadSignal(){
try{
 const d=await(await fetch("/api/work/signal")).json();
 const msgs=(d&&d.messages)||[];
const sec=document.getElementById("signal");
 sec.hidden=false;
document.getElementById("sigcount").textContent=msgs.length;
 const list=document.getElementById("sig-list");
list.textContent="";
 msgs.slice().reverse().forEach(m=>{
const r=document.createElement("div");
r.className="sig-msg";
  const t=document.createElement("span");
t.className="sm";
t.textContent=(m.mock?"[mock] ":"")+(m.message||"");
  const to=document.createElement("span");
to.className="sto2";
to.textContent=m.to||"";
  const del=document.createElement("button");
del.className="sig-del";
del.textContent="usuń (inverse)";
   del.onclick=()=>sigDelete(m.id);
  r.append(t,to,del);
list.append(r);
}
);
 clearTimeout(loadSignal._t);
loadSignal._t=setTimeout(loadSignal,10000);
}
catch(e){
clearTimeout(loadSignal._t);
loadSignal._t=setTimeout(loadSignal,20000);
}
}
loadSignal();
function whereImageSrc(url){
if(!url)return"";
 if(String(url).startsWith("data:"))return url;
 const sep=String(url).includes("?")?"&":"?";
return url+sep+"t="+Date.now();
}
async function loadWhere(){
const m=document.getElementById("where-meta");
try{
 const d=await(await fetch("/api/work/where")).json();
 const ni=d.node_identity||{
}
;
const disp=(d.display||{
}
);
 m.innerHTML="<span>host (skąd steruję): <b>"+((d.host||{
}
).hostname||"?")+"</b></span>"  +"<span>węzeł docelowy: <b>"+(d.node||"?")+"</b> ("+(ni.name||"?")+", "+(ni.routes||"?")+" tras)</span>"  +"<span>ekran węzła: <b>"+(disp.width||"?")+"×"+(disp.height||"?")+"</b></span>"  +"<span>na wierzchu: <b>"+(d.foreground||"?")+"</b></span>";
 const img=document.getElementById("where-img");
const warn=document.getElementById("where-shotwarn");
 const cap=d.capture||{
}
;
 if(cap.url){
img.src=whereImageSrc(cap.url);
img.style.display="block";
}
else{
img.style.display="none";
}
 if(cap.url){
warn.style.display="none";
}
  else{
warn.style.display="block";
warn.textContent="⚠ brak zrzutu z węzła "+(d.node||"")+" (węzeł zwrócił ścieżkę bez bajtów)";
}
 const wins=document.getElementById("where-wins");
wins.textContent="";
 (d.windows||[]).forEach(w=>{
const el=document.createElement("div");
el.className="ww"+((w.title===d.foreground)?" fg":"");
   el.textContent="• "+(w.title||JSON.stringify(w)).slice(0,60);
wins.append(el);
}
);
 if(!(d.windows||[]).length){
wins.textContent="(brak listy okien)";
}
}
catch(e){
m.textContent="błąd: "+e;
}
}
loadWhere();
async function sigSend(){
const st=document.getElementById("sig-status");
 const to=document.getElementById("sig-to").value.trim();
const message=document.getElementById("sig-msg").value.trim();
 if(!to||!message){
st.textContent="podaj odbiorcę i treść";
return;
}
st.textContent="wysyłam…";
 try{
const r=await(await fetch("/api/work/signal",{
method:"POST",headers:{
"Content-Type":"application/json"}
,   body:JSON.stringify({
action:"send",to,message}
)}
)).json();
  st.textContent=r.ok?("wysłano "+(r.mode==="mock"?"(mock)":"(signal-cli)")+" ✓ id="+(r.id||"")):("błąd: "+(r.error||"?"));
  if(r.ok){
document.getElementById("sig-msg").value="";
loadSignal();
}
}
catch(e){
st.textContent="błąd: "+e;
}
}
async function sigDelete(id){
try{
await fetch("/api/work/signal",{
method:"POST",  headers:{
"Content-Type":"application/json"}
,body:JSON.stringify({
action:"delete",id}
)}
);
loadSignal();
}
catch(e){
}
}
async function ticketCreate(){
const el=document.getElementById("nt-name");
 const name=(el.value||"").trim();
if(!name)return;
el.disabled=true;
 try{
const r=await(await fetch("/api/work/ticket/create",{
method:"POST",   headers:{
"Content-Type":"application/json"}
,body:JSON.stringify({
name}
)}
)).json();
  if(r.ok){
el.value="";
if(typeof loadQueue==="function")loadQueue();
}
  else{
alert("błąd: "+(r.error||"?"));
}
}
catch(e){
alert("błąd: "+e);
}
el.disabled=false;
el.focus();
}
async function cronAdd(){
const st=document.getElementById("cron-status");
 const schedule=document.getElementById("cron-sch").value.trim();
 const command=document.getElementById("cron-cmd").value.trim();
 const label=document.getElementById("cron-lbl").value.trim();
 if(!schedule||!command){
st.textContent="podaj harmonogram i polecenie";
return;
}
 st.textContent="dodaję…";
 try{
const r=await(await fetch("/api/work/cron",{
method:"POST",   headers:{
"Content-Type":"application/json"}
,body:JSON.stringify({
action:"add",schedule,command,label}
)}
)).json();
  st.textContent=r.ok?("dodano "+(r.cron||"")+" ✓ ("+new Date().toLocaleTimeString()+")"):("błąd: "+(r.error||"?"));
  if(r.ok){
document.getElementById("cron-cmd").value="";
loadCron();
}
}
catch(e){
st.textContent="błąd: "+e;
}
}
async function cronRemove(id){
if(!id)return;
 try{
await fetch("/api/work/cron",{
method:"POST",headers:{
"Content-Type":"application/json"}
,  body:JSON.stringify({
action:"remove",id}
)}
);
loadCron();
}
catch(e){
}
}
async function cronExport(fmt,mode){
const st=document.getElementById("cron-status");
 try{
const q="/api/work/cron/export?fmt="+fmt+(mode?("&mode="+mode):"");
  const d=await(await fetch(q)).json();
  if(!d.ok){
st.textContent="eksport: "+(d.error||"?");
return;
}
  const text=d.ics||d.csv||"";
const blob=new Blob([text],{
type:d.contentType||"text/plain"}
);
  const a=document.createElement("a");
a.href=URL.createObjectURL(blob);
a.download=d.filename||"cron-export";
  document.body.appendChild(a);
a.click();
a.remove();
  st.textContent="pobrano "+(d.filename||"")+" ("+(d.events!=null?d.events+" zdarzeń":Math.round((d.bytes||0))+" B")+")";
 }
catch(e){
st.textContent="błąd eksportu: "+e;
}
}
