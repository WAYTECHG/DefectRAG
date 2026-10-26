import {friendlyError} from './userLanguage.mjs';
let enabled=false;
export function configureLocalSync(value){enabled=value===true}
export function localSyncEnabled(){return enabled}

export async function localSyncRequest(path,options={},client,workspace,fetcher=fetch,storage=localStorage){
 const endpoint=new URL(path,location.origin).pathname;
 if((!options.method||options.method==='GET')&&(/^\/api\/(health|models|evaluation|samples|gallery)(\/|$)/.test(endpoint)||endpoint==='/api/benchmark/official'))return fetcher(path,{...options,cache:'no-store'});
 // Session namespace is random browser routing material, never an account ID.
 let session=storage.getItem('defectrag-local-browser');
 if(!/^[a-f0-9]{64}$/.test(session||'')){
  session=Array.from(crypto.getRandomValues(new Uint8Array(32)),v=>v.toString(16).padStart(2,'0')).join('');
  storage.setItem('defectrag-local-browser',session);
 }
 const {data,error}=await client.auth.getSession();
 if(error)throw new Error('Local account session could not refresh. Sign in again; saved local records are retained.');
 const headers=new Headers(options.headers||{});
 headers.set('X-DefectRAG-Session',session);headers.set('X-DefectRAG-Workspace',workspace);
 if(data.session?.access_token)headers.set('Authorization','Bearer '+data.session.access_token);
 return fetcher(path,{...options,headers,cache:'no-store'});
}

export function synchronizationText(status){
 if(!status)return 'Work saved on this computer is kept here. Sign in and verify the security code to keep this account’s private work up to date across devices.';
 if(status.state==='conflict')return 'This inspection was changed in two places. Both copies are kept. Choose Compare saved changes to decide what to keep.';
 if(status.message)return friendlyError(status.message,'Some changes could not be saved online yet. Work saved on this computer is kept. Check the connection and try again.');
 if(status.pending)return `${status.pending} change${status.pending===1?' is':'s are'} saved on this computer and waiting to be confirmed online. Keep the app open and connected until this finishes.`;
 if(status.scan_in_progress)return 'Loading more private inspections from the online account. The next check will continue where this one stopped.';
 if(status.last_synchronized)return 'Private work is up to date across this computer and the online account. New changes are checked about every 15 seconds. Team sharing is still a separate choice.';
 return 'Preparing this account’s private saved work. Nothing is shared with the team automatically.';
}
