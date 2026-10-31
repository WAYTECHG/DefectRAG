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

// Controls are the boxes a learner must reach (buttons, fields); the whole
// highlighted area counts a little so ties still prefer leaving it visible.
export function chooseCoachSpot(viewport,controls=[],target=null){
 const spots=coachSpots(viewport);
 const cost=spot=>controls.reduce((sum,box)=>sum+area(spot,box),0)*100+(target?area(spot,target):0);
 return spots.reduce((best,spot)=>cost(spot)<cost(best)?spot:best,spots[0]).name;
}
