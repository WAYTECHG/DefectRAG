// Zoom and pan maths for the inspection viewer. Pan is a percentage of the stage
// size; the image may move only as far as its enlarged edges allow.
export const ZOOM_MIN=1,ZOOM_MAX=2.5,ZOOM_STEP=.25;

export function clampPan(pan,zoom){
 const limit=Math.max(0,(zoom-1)*50);
 const clamp=v=>Math.min(limit,Math.max(-limit,Number.isFinite(v)?v:0));
 return {x:clamp(pan.x),y:clamp(pan.y)};
}

// The compare divider sits at `split` percent of the stage. The overlay is inside
// the zoomed layer, so its clip edge is converted into that layer's coordinates.
export function overlayClip(split,zoom,panX=0){
 return 50+(split-50-panX)/zoom;
}

export function nextZoom(zoom,direction){
 const value=Math.round((zoom+direction*ZOOM_STEP)*100)/100;
 return Math.min(ZOOM_MAX,Math.max(ZOOM_MIN,value));
}
