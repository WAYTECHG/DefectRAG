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
 if(!status)return 'Local records are retained. Sign in with required MFA to synchronize this account privately.';
 if(status.state==='conflict')return 'Cloud and local changes conflict. Both copies are retained until a resolution is chosen.';
 if(status.message)return status.message;
 if(status.pending)return `${status.pending} local change${status.pending===1?'':'s'} waiting for private cloud confirmation.`;
 if(status.scan_in_progress)return 'Downloading private cloud history. The next synchronization continues this scan.';
 if(status.last_synchronized)return 'Private cloud changes are synchronized. New changes are checked about every 15 seconds.';
 return 'Preparing the private local mirror. Team sharing remains a separate action.';
}
