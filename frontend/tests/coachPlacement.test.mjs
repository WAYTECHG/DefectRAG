import test from 'node:test';
import assert from 'node:assert/strict';
import {blocks,chooseCoachSpot,coachSpots,keyControls} from '../src/coachPlacement.mjs';

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

test('before a step control exists, the coach still avoids the page button that opens it (reported step 9)',()=>{
 // The review form is not shown yet; the Team row's Review button sits under the default corner.
 const review=box(1700,575,1800,620),refresh=box(1335,358,1453,406),corrective=box(1469,358,1682,406);
 const spot=chooseCoachSpot(desktop,[],null,[review,refresh,corrective]);
 const chosen=coachSpots(desktop).find(s=>s.name===spot);
 const overlaps=b=>chosen.left<b.right&&b.left<chosen.right&&chosen.top<b.bottom&&b.top<chosen.bottom;
 assert.equal(overlaps(review),false,'the Review button must stay clickable');
 assert.equal([refresh,corrective].some(overlaps),false);
});

test('sidebar links count too, so "open it in the sidebar" stays possible (live step 10)',()=>{
 // Sidebar nav items on the left; the page's own buttons sit top-right.
 const navCorrective=box(29,500,280,550),navOthers=[box(29,210,280,260),box(29,380,280,430)],pageButtons=[box(1335,358,1824,406)];
 const spot=chooseCoachSpot(desktop,[],null,[navCorrective,...navOthers,...pageButtons]);
 const chosen=coachSpots(desktop).find(s=>s.name===spot);
 const overlaps=b=>chosen.left<b.right&&b.left<chosen.right&&chosen.top<b.bottom&&b.top<chosen.bottom;
 assert.equal(overlaps(navCorrective),false);
});

test('with many step controls, the one at the screen centre stays visible (live 1366x768 sample photos)',()=>{
 const laptop={width:1366,height:768,coachWidth:380,coachHeight:380};
 // A grid of sample buttons; Candle was scrolled to the middle-right of the screen.
 const grid=[];for(let row=0;row<3;row++)for(let col=0;col<6;col++)grid.push(box(300+col*170,150+row*230,450+col*170,350+row*230));
 const candle=grid.find(b=>b.left===980&&b.top===380);
 const spot=chooseCoachSpot(laptop,grid,box(280,130,1340,850));
 const chosen=coachSpots(laptop).find(s=>s.name===spot);
 assert.equal(chosen.left<candle.right&&candle.left<chosen.right&&chosen.top<candle.bottom&&candle.top<chosen.bottom,false);
});

test('phones only swap between bottom and top, keeping full width',()=>{
 const phone={width:390,height:800,coachWidth:374,coachHeight:330};
 assert.deepEqual(coachSpots(phone).map(s=>s.name),['bottom','top']);
 assert.equal(chooseCoachSpot(phone,[box(20,600,370,650)],box(0,560,390,700)),'top');
 assert.equal(chooseCoachSpot(phone,[box(20,100,370,150)],box(0,60,390,200)),'bottom');
});

test('the card only needs to move when it hides the control in use',()=>{
 const spot=coachSpots(desktop).find(s=>s.name==='bottom-right');
 const offToTheSide=box(400,300,560,340),underTheCard=box(1600,700,1700,740);
 assert.equal(blocks(spot,keyControls(desktop,[offToTheSide])),false,'stay put while scrolling past other things');
 assert.equal(blocks(spot,keyControls(desktop,[],[underTheCard])),true,'move when the named control is underneath');
});

test('on phones only the form field nearest the middle must stay clear',()=>{
 const phone={width:390,height:844,coachWidth:374,coachHeight:250};
 const fields=[box(16,120,374,160),box(16,400,374,440),box(16,700,374,740)];
 assert.deepEqual(keyControls(phone,[],fields),[fields[1]]);
 assert.equal(keyControls(desktop,[],fields).length,3,'desktop keeps the whole form clear');
});
