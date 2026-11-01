// Reads the API envelope {data} / {error:{message}} without ever showing raw parser
// errors. Cold starts, proxies and crashes can answer with HTML or an empty body.
import {recordIssue} from './diagnostics.mjs';

const messages={
 408:'The server took too long to answer. Try again.',
 413:'The upload is too large. Use images up to 10 MB each.',
 429:'The service is busy right now. Wait a moment and try again.',
 502:'The online app is starting or restarting. Wait about a minute, then try again.',
 503:'The online app is starting or restarting. Wait about a minute, then try again.',
 504:'The server took too long to answer. Wait a moment and try again.'
};

export function statusMessage(status){
 if(messages[status])return messages[status];
 if(status>=500)return 'The server hit an unexpected problem. Try again. If it keeps happening, copy the details from Help & references and send them to the administrator.';
 if(status===401||status===403)return 'This account cannot open that. Check the sign-in in Staff workspace.';
 if(status===404)return 'That item was not found. It may have been archived or removed. Refresh and try again.';
 return 'The server reply could not be read. Refresh the page and try again.';
}

export async function readEnvelope(response,path=''){
 let text='';
 try{text=await response.text()}catch{}
 let body;
 if(text){try{body=JSON.parse(text)}catch{body=undefined}}
 if(response.ok&&body!==undefined)return body?.data;
 const detail=body?.error?.message||(typeof body?.detail==='string'?body.detail:'');
 const message=detail||statusMessage(response.ok?0:response.status);
 recordIssue('api',message,{status:response.status,path});
 throw Object.assign(new Error(message),{status:response.status});
}
