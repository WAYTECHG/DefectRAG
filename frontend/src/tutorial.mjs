// Only this dismissal preference persists. Practice data lives in practice.mjs
// for the length of the lesson and never enters a real workspace.
export const TUTORIAL_KEY='defectrag-guided-practice-v3';
let dismissedThisSession=false;
export function tutorialSeen(storage){
 if(dismissedThisSession)return true;
 try{return storage?.getItem(TUTORIAL_KEY)==='done'}catch{return false}
}
export function rememberTutorial(storage){
 dismissedThisSession=true;
 try{storage?.setItem(TUTORIAL_KEY,'done')}catch{/* The lesson can still be skipped. */}
}
// Each step completes when the matching action happens on the real screen,
// never on a timed Next button. Targets are data-tour attributes on real controls.
export function tutorialSteps(){return [
 {id:'product',page:'inspect',event:'product',target:'product',title:'Choose the product',instruction:'In Product category, choose Candle. Always choose the product that is in the photo.'},
 {id:'photo',page:'inspect',event:'photo',target:'samples',title:'Add a photo',instruction:'Below, under “Or try a sample photo”, choose the first Candle sample. For real work, use Choose an image to pick a photo from this device.'},
 {id:'inspect',page:'inspect',event:'inspect',target:'run',title:'Run the inspection',instruction:'Select Run inspection. In practice this opens a saved Candle example, so there is no AI run and no wait.'},
 {id:'compare',page:'inspect',event:'compare',target:'viewer',title:'Compare the photo and highlights',instruction:'Select Compare images, then drag the divider to compare the original photo with the highlighted areas.'},
 {id:'ask',page:'inspect',event:'ask',target:'assistant',title:'Ask the Evidence Assistant',instruction:'Choose a suggested question or type your own, then select Ask. Practice shows a prepared answer; normal work uses the real assistant.'},
 {id:'open',page:'history',event:'open',target:'history',title:'Find saved work',instruction:'Open Inspection history in the sidebar, then select the open button on the practice row. Approved Staff results save to Personal Workspace automatically.'},
 {id:'share',page:'inspect',event:'share',target:'share',title:'Share with the team',instruction:'Select Share with team. Sharing is always your choice and creates a separate Team copy; in practice nothing leaves this browser.'},
 {id:'gallery',page:'inspect',event:'gallery',target:'publish',title:'Understand public sharing',instruction:'Scroll to “Publish to community gallery”, tick the box and select Publish. In practice nothing is published; in real work anyone could see the copy.'},
 {id:'review',page:'team',event:'review',target:'review',title:'Record a Staff review',instruction:'Open Staff workspace, select Review on the practice row, choose Reviewed and “Reject: defect confirmed”, add a short note and Save review.'},
 {id:'case',page:'cases',event:'case',target:'case',title:'Create a corrective action',instruction:'In Corrective Actions choose the practice inspection marked Ready. Describe the fix, choose Alex as person responsible and You as supervisor, set a future deadline, tick the confirmation and Create corrective action.'},
 {id:'lifecycle',page:'cases',event:'lifecycle',target:'case-update',title:'Track the case to closure',instruction:'Open Details on the new case. Save each update in turn: Assigned, In Progress, Resolved and Closed, with a short note each time.'},
 {id:'batch',page:'batch',event:'batch',target:'batch',title:'Check a group of photos',instruction:'Choose Candle, enter a batch name, select Use two practice photos, then Inspect batch. No earlier single inspection is needed.'},
 {id:'alert',page:'alerts',event:'alert',target:'alerts',title:'Notice a review alert',instruction:'Select Mark as seen on a practice alert. This records that someone noticed it; it does not approve the product or close a case.'},
 {id:'finish',page:'overview',event:'finish',target:'finish',title:'Ready for real work',instruction:'Select Finish tutorial. All practice data disappears and your real workspace returns unchanged. Replay any time from Overview.'}
];}
export function newPractice(){return {started:false,step:0,caseState:null,hint:''};}
const lifecycle=['Open','Assigned','In Progress','Resolved','Closed'];
export function practiceReducer(state,action){
 if(action.type==='start')return {...newPractice(),started:true};
 if(!state.started)return state;
 const steps=tutorialSteps(),step=steps[state.step];
 if(action.type==='back')return state.step?{...state,step:state.step-1,hint:''}:state;
 if(action.type!=='complete')return state;
 // Track the practice case even when its update arrives during another step.
 if(action.event==='lifecycle'&&action.state)state={...state,caseState:action.state};
 if(action.event!==step.event)return state;
 if(step.event==='product'&&action.value!=='candle')return {...state,hint:'Choose Candle for this lesson.'};
 if(step.event==='review'&&(action.status!=='Reviewed'||action.decision!=='Reject'))
  return {...state,hint:'Saved, but this lesson needs Reviewed with “Reject: defect confirmed”. Save the review again with those choices.'};
 if(step.event==='lifecycle'&&state.caseState!=='Closed'){
  const next=lifecycle[lifecycle.indexOf(state.caseState)+1];
  return {...state,hint:next?`Saved as ${state.caseState}. Next, choose ${next} and save again.`:''};
 }
 return {...state,hint:'',step:Math.min(state.step+1,steps.length-1)};
}
