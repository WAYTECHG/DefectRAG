// Scope is a routing choice, never an authorization grant. RLS/JWT validate access.
let enabled=false,selected='personal';
export function configureWorkspace(value){enabled=value===true}
export function personalEnabled(){return enabled}
export function activeWorkspace(){return enabled?selected:'team'}
export function setWorkspace(value){
 if(!['personal','team'].includes(value))throw new Error('Invalid workspace');
 selected=value;
}

export function startPolling(load,{interval=15000,onState=()=>{},target=window,documentTarget=document}={}){
 let stopped=false,inFlight=false,again=false;
 async function refresh(){
  if(stopped)return;
  if(inFlight){again=true;return}
  if(target.navigator?.onLine===false){onState({state:'offline'});return}
  inFlight=true;onState({state:'refreshing'});
  try{const applied=await load();if(!stopped&&applied!==false)onState({state:'synced',at:Date.now()})}
  catch(error){if(!stopped)onState({state:'stale',error:error.message})}
  finally{inFlight=false;if(again&&!stopped){again=false;refresh()}}
 }
 const visible=()=>{if(!documentTarget.hidden)refresh()};
 const offline=()=>onState({state:'offline'});
 const timer=setInterval(visible,interval);
 for(const event of ['focus','online','defectrag-workspace-change'])target.addEventListener(event,visible);
 target.addEventListener('offline',offline);documentTarget.addEventListener('visibilitychange',visible);
 refresh();
 return {refresh,stop(){stopped=true;clearInterval(timer);for(const event of ['focus','online','defectrag-workspace-change'])target.removeEventListener(event,visible);target.removeEventListener('offline',offline);documentTarget.removeEventListener('visibilitychange',visible)}};
}
