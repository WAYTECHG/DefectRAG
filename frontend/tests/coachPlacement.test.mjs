import test from 'node:test';
import assert from 'node:assert/strict';
import {chooseCoachSpot,coachSpots} from '../src/coachPlacement.mjs';

const desktop={width:1900,height:900,coachWidth:470,coachHeight:380};
const box=(left,top,right,bottom)=>({left,top,right,bottom});

test('the coach stays bottom-right when nothing important is underneath',()=>{
 assert.equal(chooseCoachSpot(desktop,[box(400,300,560,340)],box(380,280,900,500)),'bottom-right');
});

test('a row Open button under the default corner moves the coach away (reported layout)',()=>{
 // Whole history card is highlighted; its Open button sits at the far right of the row.
 const card=box(352,334,1862,798),open=box(1700,630,1800,670),filters=box(440,466,1300,520);
 const spot=chooseCoachSpot(desktop,[open,filters],card);
 assert.notEqual(spot,'bottom-right');
 const chosen=coachSpots(desktop).find(s=>s.name===spot);
 const overlaps=b=>chosen.left<b.right&&b.left<chosen.right&&chosen.top<b.bottom&&b.top<chosen.bottom;
 assert.equal(overlaps(open),false,'the Open button must stay clickable');
});

test('phones only swap between bottom and top, keeping full width',()=>{
 const phone={width:390,height:800,coachWidth:374,coachHeight:330};
 assert.deepEqual(coachSpots(phone).map(s=>s.name),['bottom','top']);
 assert.equal(chooseCoachSpot(phone,[box(20,600,370,650)],box(0,560,390,700)),'top');
 assert.equal(chooseCoachSpot(phone,[box(20,100,370,150)],box(0,60,390,200)),'bottom');
});
