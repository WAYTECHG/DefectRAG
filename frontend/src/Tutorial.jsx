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
  <p id="tutorial-description">Follow the highlighted controls on each page. Completing an action opens the next step automatically.</p>
  <ul className="tutorial-points"><li>Practise checking a photo, finding saved work, sharing, Staff review and tracking a fix.</li><li>A saved public example is used. No new AI run, account sign-in, real save, sharing or email is needed.</li><li>Practice disappears when the lesson ends or the page reloads. Existing work stays separate. Skip at any time and replay from Overview.</li></ul>
  <div className="tutorial-footer"><button type="button" className="text-button" onClick={onDismiss}>Skip tutorial</button><button type="button" className="primary" onClick={onStart}>Start guided practice <ArrowRight size={16}/></button></div>
 </dialog>;
}
