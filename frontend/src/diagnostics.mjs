// A small, private record of recent problems for the Help page's "Copy details"
// button. It never stores emails, tokens, file names, notes or photos.
const MAX=15;
const issues=[];

/* global __APP_BUILD__ */
export const build=typeof __APP_BUILD__==='object'&&__APP_BUILD__?__APP_BUILD__:{version:'dev',commit:'local',built:''};

const scrub=value=>String(value||'')
 .replace(/[\w.+-]+@[\w-]+\.[\w.-]+/g,'[email]')
 .replace(/eyJ[\w-]+\.[\w-]+\.[\w-]+/g,'[token]')
 .replace(/(bearer|apikey|key|token)=?\s*[\w-]{16,}/gi,'$1 [hidden]')
 .slice(0,300);

export function recordIssue(kind,message,extra={}){
 const path=String(extra.path||'').split('?')[0].replace(/[0-9a-f]{8,}/gi,':id');
 issues.push({at:new Date().toISOString(),kind,message:scrub(message),status:extra.status??null,path});
 if(issues.length>MAX)issues.splice(0,issues.length-MAX);
}

export function recentIssues(){return issues.slice()}
export function clearIssues(){issues.length=0}

export function diagnosticReport(context={},env=globalThis){
 const nav=env.navigator||{},screen=env.innerWidth?env.innerWidth+'×'+env.innerHeight:'unknown';
 const lines=[
  'DefectRAG diagnostic details',
  'Version: '+build.version+' · build '+build.commit+(build.built?' · '+build.built:''),
  'Page: '+(context.page||'unknown')+' · mode: '+(context.mode||'unknown')+' · sync: '+(context.sync||'unknown'),
  'Signed in: '+(context.signedIn?'yes':'no')+' · workspace: '+(context.workspace||'unknown'),
  'Screen: '+screen+' · theme: '+(context.theme||'unknown')+' · text size: '+(context.textSize?Math.round(context.textSize*100)+'%':'unknown'),
  'Browser: '+scrub(nav.userAgent||'unknown'),
  'Online: '+(nav.onLine===false?'no':'yes'),
  'Time: '+new Date().toISOString(),
  '',
  'Recent problems ('+issues.length+'):'
 ];
 if(!issues.length)lines.push('none recorded in this tab');
 for(const item of issues.slice().reverse())lines.push('- '+item.at+' · '+item.kind+(item.status?' '+item.status:'')+(item.path?' · '+item.path:'')+' · '+item.message);
 return lines.join('\n');
}
