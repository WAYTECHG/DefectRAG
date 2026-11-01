import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {readEnvelope,statusMessage} from '../src/http.mjs';
import {recordIssue,recentIssues,clearIssues,diagnosticReport} from '../src/diagnostics.mjs';
import {clampPan,overlayClip,nextZoom,ZOOM_MAX} from '../src/viewerMath.mjs';

test('server replies: data, server messages and unreadable pages all become clear results',async()=>{
 assert.deepEqual(await readEnvelope(Response.json({data:{ok:1}})),{ok:1});
 await assert.rejects(readEnvelope(Response.json({error:{message:'Batch name taken'}},{status:409})),e=>e.status===409&&e.message==='Batch name taken');
 await assert.rejects(readEnvelope(Response.json({detail:'Not allowed'},{status:400})),/Not allowed/);
 for(const status of [502,503])await assert.rejects(readEnvelope(new Response('<html>busy</html>',{status})),e=>e.status===status&&/starting or restarting/.test(e.message));
 await assert.rejects(readEnvelope(new Response('',{status:500})),/unexpected problem/);
 await assert.rejects(readEnvelope(new Response('<html>ok?</html>',{status:200})),/could not be read/);
 assert.match(statusMessage(413),/10 MB/);assert.match(statusMessage(429),/busy/);
});

test('support details are useful but never carry private values',()=>{
 clearIssues();
 recordIssue('api','Denied for wilbert@example.com token eyJabc.def.ghi',{status:403,path:'/api/inspections/0123456789abcdef0123/messages?x=1'});
 const [item]=recentIssues();
 assert.equal(item.path,'/api/inspections/:id/messages');assert.doesNotMatch(item.message,/wilbert@|eyJabc/);
 for(let i=0;i<30;i++)recordIssue('api','x'+i);
 assert.equal(recentIssues().length,15);
 const report=diagnosticReport({page:'cases',mode:'cloud_session_workspace',sync:'stale',signedIn:true,workspace:'team',theme:'dark',textSize:.8},{navigator:{userAgent:'Test',onLine:true},innerWidth:390,innerHeight:844});
 for(const part of ['Version:','Page: cases','sync: stale','Screen: 390×844','text size: 80%','Recent problems (15)'])assert.ok(report.includes(part),part);
});

test('viewer zoom and pan stay inside the photo, and the compare split matches the divider',()=>{
 assert.equal(nextZoom(1,-1),1);assert.equal(nextZoom(2.5,1),ZOOM_MAX);assert.equal(nextZoom(1,1),1.25);
 assert.deepEqual(clampPan({x:90,y:-90},2),{x:50,y:-50});assert.deepEqual(clampPan({x:10,y:10},1),{x:0,y:0});
 assert.equal(overlayClip(50,2,0),50);assert.equal(overlayClip(30,1,0),30);
 // At 2× with the photo moved 20% right, the divider at 30% of the stage cuts the photo at its 30% point.
 const clip=overlayClip(30,2,20),stagePoint=50+20+2*(clip-50);assert.equal(stagePoint,30);
});

test('pages are wrapped so one failure never blanks the app; menu and old messages are handled',async()=>{
 const main=await readFile(new URL('../src/main.jsx',import.meta.url),'utf8');
 assert.ok(main.includes('<ErrorBoundary resetKey={page}'));assert.ok(main.includes('</ErrorBoundary>'));
 assert.ok(main.includes("aria-controls=\"app-nav\""));assert.ok(main.includes("setMenuOpen(false)"));
 assert.ok(main.includes("const navigate=()=>{setPage(current=>pageFromLocation(current));setError('');setNotice('')"));
 // Follow-up refreshes never turn a saved action into a reported failure.
 assert.ok(!main.includes('workspaceChanged();await refresh()}}/></section>}'));
 // The cloud build rewrites these exact lines; they must stay.
 assert.ok(main.includes('return fetch(url(path),options)'));assert.ok(main.includes('const url=assetUrl;'));
});
