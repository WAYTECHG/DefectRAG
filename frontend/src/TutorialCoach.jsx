import React,{useEffect,useRef,useState} from 'react';
import {ArrowLeft,BookOpen,Crosshair,X} from 'lucide-react';
import {tutorialSteps} from './tutorial.mjs';
import {blocks,chooseCoachSpot,coachSpots,keyControls} from './coachPlacement.mjs';

const CONTROLS='button,a[href],input,select,textarea,[role=button],[tabindex="0"]';

const pageNames={inspect:'Image inspection',history:'Inspection history',team:'Staff workspace',cases:'Corrective Actions',batch:'Batch inspection',alerts:'Review alerts',overview:'Overview'};
// Coach card over the real screens; highlights the real control for each step.
export default function TutorialCoach({state,page,onGo,onSkip,onFinish,onBack}){
 const steps=tutorialSteps(),step=steps[state.step],heading=useRef(null),card=useRef(null),text=useRef(null),spotRef=useRef('bottom-right');
 const [spot,setSpot]=useState('bottom-right'),[more,setMore]=useState(false),[clipped,setClipped]=useState(false);
 const onPage=page===step.page||step.target==='finish';
 useEffect(()=>{heading.current?.focus({preventScroll:true});setMore(false)},[state.step]);
 // Offer More only when the compact two-line text is actually cut off.
 useEffect(()=>{const check=()=>{const el=text.current;setClipped(!!el&&el.scrollHeight>el.clientHeight+1)};check();window.addEventListener('resize',check);return()=>window.removeEventListener('resize',check)},[state.step,more]);
 // Extra page room (phones) so any control can be scrolled clear of the card.
 useEffect(()=>{document.body.classList.add('coach-open');return()=>document.body.classList.remove('coach-open')},[]);
 useEffect(()=>{
  // Real pages re-render while polling, so re-apply the highlight briefly each second.
  let shown=null;
  const mark=()=>{const target=onPage?document.querySelector('[data-tour="'+step.target+'"]'):null;
   if(target!==shown){shown?.classList.remove('tour-target');target?.classList.add('tour-target');shown=target}
   place(target)};
  // The card stays put; it moves only when it hides the control needed right now,
  // and then to the corner that hides the fewest controls.
  const place=target=>{
   const box=card.current?.getBoundingClientRect();if(!box)return;
   const visible=list=>[...list].filter(el=>el.offsetParent!==null&&!card.current.contains(el)).map(el=>el.getBoundingClientRect());
   const controls=target?visible([...target.querySelectorAll(CONTROLS),...(target.matches(CONTROLS)?[target]:[])]):[];
   // Page and sidebar controls: steps often say "open X in the sidebar".
   const pageControls=visible(document.querySelectorAll(['main','nav'].flatMap(area=>CONTROLS.split(',').map(c=>area+' '+c)).join(',')));
   const find=f=>visible([...document.querySelectorAll(f.selector)].filter(el=>!f.text||el.textContent.toLowerCase().includes(f.text)));
   const focus=[].concat(step.focus||[]).map(find).find(found=>found.length)||[];
   const viewport={width:window.innerWidth,height:window.innerHeight,coachWidth:box.width,coachHeight:box.height};
   const here=coachSpots(viewport).find(s=>s.name===spotRef.current);
   if(here&&!blocks(here,keyControls(viewport,controls,focus)))return;
   spotRef.current=chooseCoachSpot(viewport,controls,target?.getBoundingClientRect()||null,pageControls,focus);setSpot(spotRef.current);
  };
  // Re-check only once scrolling or resizing has settled, never mid-scroll.
  let settle;const reposition=()=>{clearTimeout(settle);settle=setTimeout(()=>place(shown),300)};
  mark();const timer=setInterval(mark,1000);
  window.addEventListener('scroll',reposition,{passive:true});window.addEventListener('resize',reposition);
  return()=>{clearInterval(timer);clearTimeout(settle);window.removeEventListener('scroll',reposition);window.removeEventListener('resize',reposition);shown?.classList.remove('tour-target')};
 },[step.target,onPage]);
 // On phones the card covers the lower screen, so bring the control to the top.
 function show(){document.querySelector('[data-tour="'+step.target+'"]')?.scrollIntoView({block:window.innerWidth<=680?'start':'center',behavior:'smooth'})}
 return <aside ref={card} className={'tutorial-coach at-'+spot} role="dialog" aria-modal="false" aria-labelledby="coach-title">
  <div className="section-title"><span className="subtle-tag"><BookOpen size={13}/> PRACTICE · STEP {state.step+1} OF {steps.length}</span><button type="button" className="icon-button" aria-label="Skip tutorial" onClick={onSkip}><X size={17}/></button></div>
  <progress aria-label="Practice progress" value={state.step+1} max={steps.length}/>
  <h2 ref={heading} tabIndex={-1} id="coach-title">{step.title}</h2>
  <p ref={text} aria-live="polite" className={'coach-text'+(more?' open':'')}>{step.instruction}</p>
  {(clipped||more)&&<button type="button" className="text-button coach-more" aria-expanded={more} onClick={()=>setMore(value=>!value)}>{more?'Less':'More'}</button>}
  {state.hint&&<p className="coach-hint" role="status">{state.hint}</p>}
  {!onPage&&<p className="caption">This step is on {pageNames[step.page]}.</p>}
  <div className="coach-actions">
   <button type="button" className="text-button" disabled={!state.step} onClick={onBack}><ArrowLeft size={14}/> Previous</button>
   {step.target==='finish'?<button type="button" className="primary" data-tour="finish" onClick={onFinish}>Finish tutorial</button>
    :onPage?<button type="button" className="secondary" onClick={show}><Crosshair size={15}/> Show me</button>
    :<button type="button" className="primary" onClick={()=>onGo(step.page)}>Go to {pageNames[step.page]}</button>}
  </div>
  <small>Practice data only · nothing is saved, shared, published or emailed. Your real work returns when the lesson ends.</small>
 </aside>;
}
