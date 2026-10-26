import {nextCaseStates} from './correctiveActions.mjs';

// Only this dismissal preference persists. Practice never enters a workspace.
export const TUTORIAL_KEY='defectrag-guided-practice-v2';
let dismissedThisSession=false;
export function tutorialSeen(storage){
 if(dismissedThisSession)return true;
 try{return storage?.getItem(TUTORIAL_KEY)==='done'}catch{return false}
}
export function rememberTutorial(storage){
 dismissedThisSession=true;
 try{storage?.setItem(TUTORIAL_KEY,'done')}catch{/* The lesson can still be skipped. */}
}
export const practiceRecord=Object.freeze({
 id:'practice-candle',category:'candle',verdict:'Anomalous',
 score:0.046729326248168945,threshold:0.04235455393791199,
 model_id:'dinov3-normal-bank-candle-v1',
 image_url:'./showcase/images/7dbb6f27253b450698a1a503cfa9a8c8.jpg',
 heatmap_url:'./showcase/images/7dbb6f27253b450698a1a503cfa9a8c8_heatmap.jpg',
 source:'Bundled public VisA example, measured 16 October 2026. No new prediction.'
});
// Completion follows the matching user action, never a timed Next button.
export function tutorialSteps(){return [
 {id:'product',page:'inspect',event:'product',title:'Choose the product',instruction:'In Product category, choose Candle. The photo in this lesson shows candles.',target:'product'},
 {id:'photo',page:'inspect',event:'photo',title:'Add the sample photo',instruction:'Select Use sample photo. For normal work, the photo picker accepts a photo from the device.',target:'photo'},
 {id:'inspect',page:'inspect',event:'inspect',title:'Run the inspection',instruction:'Select Run inspection. Practice opens an existing measured example, so there is no wait for a new AI check.',target:'run'},
 {id:'compare',page:'inspect',event:'compare',title:'Compare the photo and highlights',instruction:'Select Compare images below the result, then drag the divider to compare the original and highlighted areas.',target:'compare'},
 {id:'ask',page:'inspect',event:'ask',title:'Try the Evidence Assistant',instruction:'Type a question about the score or highlights, then select Ask. This lesson shows a labelled teaching answer; normal work uses the Evidence Assistant.',target:'ask'},
 {id:'save',page:'inspect',event:'save',title:'Find the private copy',instruction:'Signed-in inspections save in Personal Workspace automatically. The lesson keeps a temporary private copy. Select Inspection history in the sidebar to find it. For real work, check that online saving has completed.',target:'history-nav'},
 {id:'history',page:'history',event:'open',title:'Find the saved result',instruction:'Inspection history is now open. Select Open inspection on the practice row to return to its photo and result.',target:'history'},
 {id:'share',page:'inspect',event:'share',title:'Choose whether to share',instruction:'Select Share with team (practice). Real sharing is always an explicit choice, requires approved Staff access and creates a separate Team copy.',target:'share'},
 {id:'review',page:'team',event:'review',title:'Save a Staff review',instruction:'Set Review status to Reviewed, Decision to Reject, and add a short note. Then select Save review (practice). An unusual model result alone is not a confirmed defect.',target:'review'},
 {id:'case',page:'cases',event:'case',title:'Create a corrective action',instruction:'Describe the problem, choose a person responsible and supervisor, set a future due date, and confirm the practice defect. Then create the practice case.',target:'case'},
 {id:'progress',page:'cases',event:'progress',title:'Record progress',instruction:'Choose In Progress, add what is being done, and save the case update. Real case edits are limited to the owner, supervisor or a Developer.',target:'progress'},
 {id:'resolve',page:'cases',event:'resolve',title:'Record the fix',instruction:'Choose Resolved and describe the fix, then save. This updates the case; it does not prove that an email has been delivered.',target:'progress'},
 {id:'close',page:'cases',event:'close',title:'Close the completed case',instruction:'Choose Closed, record the final check, then save. The practice history keeps each step.',target:'progress'},
 {id:'batch',page:'batch',event:'batch',title:'Check a group of photos',instruction:'Enter a batch name, select Add two sample photos, then Inspect batch. Batch inspection accepts new photos; no earlier single inspection is needed. It is not a live camera.',target:'batch'},
 {id:'alert',page:'alerts',event:'alert',title:'Notice a review alert',instruction:'Select Mark as seen on the practice alert. This records that it was noticed; it does not approve the product or close a case.',target:'alert'},
 {id:'gallery',page:'gallery',event:'gallery',title:'Understand public sharing',instruction:'Tick the box confirming that a gallery copy is visible to anyone, then select Continue. No practice image will be published.',target:'gallery'},
 {id:'finish',page:'overview',event:'finish',title:'Ready for normal work',instruction:'Select Finish tutorial to return to the untouched workspace. Model performance, Official benchmark and Help & references remain in the sidebar.',target:'finish'}
 ];}
export function newPractice(){return {started:false,step:0,past:[],category:'',photo:false,inspected:false,compared:false,answer:false,question:'',saved:false,opened:false,shared:false,reviewStatus:'Needs review',decision:'Pending',reviewNote:'',reviewed:false,description:'',owner:'',supervisor:'',due:'',confirmed:false,caseState:null,caseHistory:[],caseChoice:'',caseNote:'',batchName:'',batchPhotos:false,batchDone:false,alertSeen:false,publicConsent:false,error:''};}
const fields=new Set(['category','question','reviewStatus','decision','reviewNote','description','owner','supervisor','due','confirmed','caseChoice','caseNote','batchName','publicConsent']);
export function practiceReducer(state,action){
 if(action.type==='start')return {...newPractice(),started:true};
 if(action.type==='field'&&fields.has(action.name))return {...state,[action.name]:action.value,error:''};
 if(action.type==='batch-photos')return {...state,batchPhotos:true,error:''};
 if(action.type==='back'){
  const previous=state.past[state.step-1];
  if(!previous)return state;
  return {...previous,past:state.past.slice(0,state.step-1),...(previous.step===0?{category:''}:{}),error:''};
 }
 const step=tutorialSteps()[state.step];
 if(action.type==='navigate')return step.event==='save'&&action.page==='history'?practiceReducer(state,{type:'complete',event:'save'}):state;
 if(action.type!=='complete'||action.event!==step.event||!state.started)return state;
 let patch={},error='';
 switch(step.event){
  case 'product':if(state.category!=='candle')return state;break;
  case 'photo':patch={photo:true};break;
  case 'inspect':if(!state.photo||state.category!=='candle')return state;patch={inspected:true};break;
  case 'compare':if(!state.inspected||action.value!==true)return state;patch={compared:true};break;
  case 'ask':if(!state.inspected||state.question.trim().length<3)error='Enter a short question first.';else patch={answer:true};break;
  case 'save':if(!state.inspected)return state;patch={saved:true};break;
  case 'open':if(!state.saved)return state;patch={opened:true};break;
  case 'share':if(!state.saved||!state.opened)return state;patch={shared:true};break;
  case 'review':if(!state.shared)return state;if(state.reviewStatus!=='Reviewed'||state.decision!=='Reject'||state.reviewNote.trim().length<3)error='Choose Reviewed and Reject, then add a short review note.';else patch={reviewed:true};break;
  case 'case':if(!state.reviewed)return state;
   if(state.description.trim().length<10||!['Alex (practice)','Sam (practice)'].includes(state.owner)||!['Alex (practice)','Sam (practice)'].includes(state.supervisor)||!Number.isFinite(Date.parse(state.due))||Date.parse(state.due)<=(action.now??Date.now())||state.confirmed!==true)error='Complete the description, assignments, future due date and confirmation.';
   else patch={caseState:'Assigned',caseHistory:[{state:'Assigned',note:state.description}],caseChoice:'',caseNote:''};break;
  case 'progress':case 'resolve':case 'close':{
   const target={progress:'In Progress',resolve:'Resolved',close:'Closed'}[step.event];
   if(state.caseChoice!==target||!nextCaseStates(state.caseState).includes(target)||state.caseNote.trim().length<3)error='Choose '+target+' and enter a short update.';
   else patch={caseState:target,caseHistory:[...state.caseHistory,{state:target,note:state.caseNote}],caseChoice:'',caseNote:''};break;
  }
  case 'batch':if(!state.batchName.trim()||!state.batchPhotos)error='Enter a batch name and add the two sample photos.';else patch={batchDone:true};break;
  case 'alert':patch={alertSeen:true};break;
  case 'gallery':if(state.publicConsent!==true)error='Confirm that a gallery copy would be public.';break;
 }
 if(error)return {...state,error};
 const snapshot={...state};delete snapshot.past;
 return {...state,...patch,error:'',past:[...state.past.slice(0,state.step),snapshot],step:Math.min(state.step+1,tutorialSteps().length-1)};
}
