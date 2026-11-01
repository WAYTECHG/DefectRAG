import React,{useEffect,useRef} from 'react';
import {BookOpen,X,ArrowRight} from 'lucide-react';

export default function Tutorial({open,onDismiss,onStart}){
 const dialog=useRef(null),title=useRef(null);
 useEffect(()=>{
  if(open){if(!dialog.current.open)dialog.current.showModal();title.current?.focus({preventScroll:true})}
  else if(dialog.current.open)dialog.current.close();
 },[open]);
 return <dialog ref={dialog} className="tutorial-dialog" aria-labelledby="tutorial-title" aria-describedby="tutorial-description"
  onCancel={event=>{event.preventDefault();onDismiss()}} onClose={()=>{if(open)onDismiss()}}>
  <div className="tutorial-top"><span className="subtle-tag">GUIDED PRACTICE</span><button type="button" className="icon-button" aria-label="Close tutorial" onClick={onDismiss}><X size={20}/></button></div>
  <div className="tutorial-icon"><BookOpen size={30} aria-hidden="true"/></div>
  <h2 ref={title} tabIndex={-1} id="tutorial-title">Learn by doing</h2>
  <p id="tutorial-description">Practise the real steps in about 3 minutes. A guide points to the next button.</p>
  <ul className="tutorial-points"><li>Check a photo, share it, review it, and track the fix.</li><li>It is only practice. Nothing is saved, shared or emailed.</li><li>Skip any time. Replay it from Overview.</li></ul>
  <div className="tutorial-footer"><button type="button" className="text-button" onClick={onDismiss}>Skip tutorial</button><button type="button" className="primary" onClick={onStart}>Start guided practice <ArrowRight size={16}/></button></div>
 </dialog>;
}
