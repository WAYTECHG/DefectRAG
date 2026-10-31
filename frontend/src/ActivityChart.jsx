import React from 'react';

const W=1000,H=200;
// Smooth line through the points (Catmull-Rom converted to cubic Bezier).
function curve(points){
 if(points.length<2)return points.length?`M${points[0][0]} ${points[0][1]}`:'';
 let d=`M${points[0][0]} ${points[0][1]}`;
 for(let i=0;i<points.length-1;i++){
  const [p0,p1,p2,p3]=[points[i-1]||points[i],points[i],points[i+1],points[i+2]||points[i+1]];
  d+=` C${p1[0]+(p2[0]-p0[0])/6} ${p1[1]+(p2[1]-p0[1])/6} ${p2[0]-(p3[0]-p1[0])/6} ${p2[1]-(p3[1]-p1[1])/6} ${p2[0]} ${p2[1]}`;
 }
 return d;
}
const label=key=>new Date(key+'T00:00').toLocaleDateString(undefined,{day:'numeric',month:'short'});

export default function ActivityChart({series}){
 const max=Math.max(1,...series.map(s=>s.total));
 if(!series.some(s=>s.total))return <div className="chart-empty">No inspections in this period yet.</div>;
 const x=i=>series.length===1?W/2:i*W/(series.length-1),y=v=>H-6-(v/max)*(H-24);
 const line=key=>curve(series.map((s,i)=>[x(i),y(s[key])]));
 const area=key=>line(key)+` L${W} ${H} L0 ${H}Z`;
 const total=series.reduce((n,s)=>n+s.total,0),unusual=series.reduce((n,s)=>n+s.unusual,0);
 return <figure style={{margin:0}} aria-label={`${total} inspections in this period, ${unusual} unusual or close to the limit`}>
  <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img" aria-hidden="true">
   <defs>
    <linearGradient id="chart-all" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="var(--chart-2)" stopOpacity=".35"/><stop offset="1" stopColor="var(--chart-2)" stopOpacity=".03"/></linearGradient>
    <linearGradient id="chart-unusual" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="var(--bad)" stopOpacity=".3"/><stop offset="1" stopColor="var(--bad)" stopOpacity=".03"/></linearGradient>
   </defs>
   {[.25,.5,.75].map(f=><line key={f} x1="0" x2={W} y1={H*f} y2={H*f} stroke="var(--border)" strokeWidth="1" vectorEffect="non-scaling-stroke"/>)}
   <path d={area('total')} fill="url(#chart-all)" stroke="var(--chart-2)" strokeWidth="2" vectorEffect="non-scaling-stroke"/>
   <path d={area('unusual')} fill="url(#chart-unusual)" stroke="var(--bad)" strokeWidth="2" vectorEffect="non-scaling-stroke"/>
  </svg>
  <div className="chart-axis"><span>{label(series[0].date)}</span><span>{label(series[Math.floor(series.length/2)].date)}</span><span>{label(series.at(-1).date)}</span></div>
  <figcaption className="chart-legend"><span><i style={{background:'var(--chart-2)'}}/>All results · {total}</span><span><i style={{background:'var(--bad)'}}/>Unusual or closer look · {unusual}</span></figcaption>
 </figure>;
}
