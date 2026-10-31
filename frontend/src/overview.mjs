// Overview figures derived from data the dashboard already loads.
const pad=n=>String(n).padStart(2,'0');
const dayKey=d=>d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate());

export function overviewCards(stats={},{showcase=false}={}){
 const total=stats.total||0,counts=stats.counts||{};
 const share=n=>total?Math.round(n/total*100)+'%':null;
 const batches=(stats.batches||[]).filter(b=>b.batch).length;
 return [
  {title:'Inspections',value:total,share:null,tone:'',line:showcase?'Previously measured examples':'Saved in this workspace',detail:batches?batches+' named batch'+(batches===1?'':'es'):'Single photos and batches'},
  {title:'Looks normal',value:counts.Good||0,share:share(counts.Good||0),tone:'ok',line:'Within the review limit',detail:'No action needed'},
  {title:'Unusual appearance',value:counts.Anomalous||0,share:share(counts.Anomalous||0),tone:'bad',line:'Staff review recommended',detail:'Check the highlighted areas'},
  {title:'Needs a closer look',value:counts.Uncertain||0,share:share(counts.Uncertain||0),tone:'warn',line:'Close to the review limit',detail:'Check the photo again'}];
}

// One bucket per local calendar day, oldest first, for the last `days` days.
export function dailyActivity(records=[],days=30,now=new Date()){
 const buckets=[],index={};
 for(let i=days-1;i>=0;i--){const d=new Date(now.getFullYear(),now.getMonth(),now.getDate()-i);const key=dayKey(d);index[key]=buckets.length;buckets.push({date:key,total:0,unusual:0})}
 for(const r of records){
  const t=new Date(r.created_at);if(!Number.isFinite(t.getTime()))continue;
  const at=index[dayKey(t)];if(at===undefined)continue;
  buckets[at].total++;if(r.verdict==='Anomalous'||r.verdict==='Uncertain')buckets[at].unusual++;
 }
 return buckets;
}

export const overviewTabs=[['recent','Recent',()=>true],['unusual','Unusual',r=>r.verdict==='Anomalous'],['closer','Closer look',r=>r.verdict==='Uncertain']];
export function overviewRows(records=[],tab='recent',limit=5){
 const rule=(overviewTabs.find(([id])=>id===tab)||overviewTabs[0])[2];
 return records.filter(rule).slice(0,limit);
}
