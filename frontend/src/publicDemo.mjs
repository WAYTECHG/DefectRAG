// Visibility only; native authorization and per-browser backend isolation still apply.
export function publicDemoAvailable(health,access){
 return Boolean((health?.mode==='cloud_session_workspace'||health?.local_sync_enabled===true)&&access?.state==='guest');
}
