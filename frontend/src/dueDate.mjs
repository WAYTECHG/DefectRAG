// Due-date helpers for Corrective Actions. Values stay local "YYYY-MM-DDTHH:mm",
// the same shape the old datetime-local field produced.
export const DEFAULT_DUE_TIME='17:00';
export const dueShortcuts=[{label:'Tomorrow',days:1},{label:'In 3 days',days:3},{label:'In 1 week',days:7},{label:'In 2 weeks',days:14}];
const pad=n=>String(n).padStart(2,'0');
export const localDate=d=>d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate());
export function shortcutDate(days,now=new Date()){const d=new Date(now);d.setDate(d.getDate()+days);return localDate(d)}
export const joinDue=(date,time)=>date?date+'T'+(time||DEFAULT_DUE_TIME):'';
export const dueParts=value=>({date:value?value.slice(0,10):'',time:value?value.slice(11,16):''});
export const timeLabel=t=>{const [h,m]=t.split(':').map(Number);return (h%12||12)+':'+pad(m)+' '+(h<12?'AM':'PM')};
// Working-hours list in 30-minute steps; an existing off-grid time is kept selectable.
export function timeOptions(current){
 const list=[];for(let m=7*60;m<=20*60;m+=30)list.push(pad(Math.floor(m/60))+':'+pad(m%60));
 if(current&&/^\d\d:\d\d$/.test(current)&&!list.includes(current))list.push(current);
 return list.sort();
}
export function relativeDay(value,now=new Date()){
 const days=Math.round((new Date(value.slice(0,10)+'T00:00')-new Date(localDate(now)+'T00:00'))/86400000);
 return days===0?'today':days===1?'tomorrow':days>1?'in '+days+' days':days===-1?'yesterday':Math.abs(days)+' days ago';
}
export function describeDue(value,now=new Date()){
 if(!value||!Number.isFinite(Date.parse(value)))return '';
 // Built from parts: browsers disagree on commas in the full en-GB format.
 const d=new Date(value.slice(0,10)+'T00:00'),name=(o)=>d.toLocaleDateString('en-GB',o);
 return name({weekday:'long'})+', '+d.getDate()+' '+name({month:'short'})+' '+d.getFullYear()+' at '+timeLabel(value.slice(11,16))+' · '+relativeDay(value,now);
}
