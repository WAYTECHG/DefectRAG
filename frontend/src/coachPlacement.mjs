// Chooses the screen corner for the tutorial coach card so it covers as little of
// the highlighted step's controls as possible. Pure geometry; no DOM access.
export const COACH_MARGIN=24,PHONE_MARGIN=8,PHONE_WIDTH=680;
const area=(a,b)=>Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left))*Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));

export function coachSpots({width,height,coachWidth,coachHeight}){
 if(width<=PHONE_WIDTH){
  const m=PHONE_MARGIN,box=top=>({left:m,right:width-m,top,bottom:top+coachHeight});
  return [{name:'bottom',...box(height-m-coachHeight)},{name:'top',...box(m)}];
 }
 const m=COACH_MARGIN,box=(left,top)=>({left,top,right:left+coachWidth,bottom:top+coachHeight});
 return [{name:'bottom-right',...box(width-m-coachWidth,height-m-coachHeight)},{name:'bottom-left',...box(m,height-m-coachHeight)},
  {name:'top-right',...box(width-m-coachWidth,m)},{name:'top-left',...box(m,m)}];
}

// Controls are the boxes a learner must reach (buttons, fields) inside the
// highlighted step. Other page controls also count, because a step's control can
// appear only after its first click (e.g. a row's Review button opens the form).
// The highlighted area itself counts a little so ties still leave it visible.
// The control the learner needs now: the step's named control, otherwise the
// step control nearest the screen centre (people scroll their work into view).
export function keyControls(viewport,controls=[],focus=[]){
 const centre=b=>Math.hypot((b.left+b.right)/2-viewport.width/2,(b.top+b.bottom)/2-viewport.height/2);
 const nearestOf=boxes=>{const inView=boxes.filter(b=>b.bottom>0&&b.top<viewport.height&&b.right>0&&b.left<viewport.width);
  const nearest=inView.reduce((best,b)=>!best||centre(b)<centre(best)?b:best,null);return nearest?[nearest]:[]};
 // Phones have no room to keep a whole form clear, so protect the field in use.
 if(focus.length)return viewport.width<=PHONE_WIDTH&&focus.length>1?nearestOf(focus):focus;
 return nearestOf(controls);
}

// True when the card at this spot hides any of the given boxes.
export const blocks=(spot,boxes)=>boxes.some(box=>area(spot,box)>0);

export function chooseCoachSpot(viewport,controls=[],target=null,pageControls=[],focus=[]){
 const spots=coachSpots(viewport);
 const covered=(spot,boxes)=>boxes.reduce((sum,box)=>sum+area(spot,box),0);
 const key=keyControls(viewport,controls,focus);
 const cost=spot=>covered(spot,key)*1000+covered(spot,controls)*100+covered(spot,pageControls)*10+(target?area(spot,target):0);
 return spots.reduce((best,spot)=>cost(spot)<cost(best)?spot:best,spots[0]).name;
}
