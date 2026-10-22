import React from 'react';

export default function RefreshNotice({errors=[],block,refreshing,onRetry,onAccount,onPersonal,showAccess=true}){
 if(errors.length)return <div className="error" role="alert">
  Could not refresh: {errors.join(', ')}. Last loaded data may be outdated.{' '}
  <button className="text-button" disabled={refreshing} aria-busy={refreshing} onClick={onRetry}>{refreshing?'Refreshing…':'Retry refresh'}</button>
 </div>;
 if(!block||!showAccess)return null;
 return <div className={block.failed?'error':'note'} role={block.failed?'alert':'status'}>
  <div>{block.reason}{' '}
   {block.action==='account'&&<button className="text-button" onClick={onAccount}>Open Staff workspace</button>}
   {block.action==='personal'&&<button className="text-button" onClick={onPersonal}>Switch to Personal Workspace</button>}
   {block.retry&&<button className="text-button" disabled={refreshing} aria-busy={refreshing} onClick={onRetry}>{refreshing?'Refreshing…':'Retry refresh'}</button>}
  </div>
 </div>;
}
