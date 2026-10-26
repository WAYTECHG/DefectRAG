// Navigation/visibility only. Native Staff/AAL2/RLS checks remain authoritative.
// An explicit false still disables the interface; older configs may omit it.
export const caseInterfaceEnabled=(config={})=>config?.correctiveActionsEnabled!==false;

export const sharedAssistantAvailable=(health,showcase=false)=>!showcase&&
 Boolean(health?.mode==='cloud_session_workspace'||health?.local_sync_enabled);

export function focusInspectionDetails(element){
 if(!element)return;
 element.focus({preventScroll:true});
 const reduced=globalThis.window?.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
 element.scrollIntoView({block:'start',behavior:reduced?'auto':'smooth'});
}
