import React,{useEffect,useRef,useState} from 'react';
import {Expand,SplitSquareHorizontal,X,ZoomIn,ZoomOut} from 'lucide-react';
import {clampPan,overlayClip,nextZoom,ZOOM_MIN,ZOOM_MAX} from './viewerMath.mjs';

// Zoom enlarges the photo; drag (mouse or finger) moves around it. In compare
// mode the divider and the split always line up, at any zoom and position.
export default function InspectionViewer({record,url,heatmap,onComparisonUsed}){
 const [compare,setCompare]=useState(false),[position,setPosition]=useState(50),[zoom,setZoom]=useState(1),[pan,setPan]=useState({x:0,y:0}),[expanded,setExpanded]=useState(false);
 const dialog=useRef(null),drag=useRef(null);
 useEffect(()=>{setZoom(1);setPan({x:0,y:0});setPosition(50)},[record.id]);
 useEffect(()=>{if(expanded)dialog.current?.showModal();else dialog.current?.close()},[expanded]);
 const movable=zoom>1&&!compare;
 function changeZoom(direction){const next=nextZoom(zoom,direction);setZoom(next);setPan(value=>clampPan(value,next))}
 function resetView(){setZoom(1);setPan({x:0,y:0})}
 function start(e){
  if(!movable)return;
  e.currentTarget.setPointerCapture?.(e.pointerId);
  drag.current={x:e.clientX,y:e.clientY,pan,w:e.currentTarget.clientWidth||1,h:e.currentTarget.clientHeight||1};
 }
 function move(e){const d=drag.current;if(!d)return;setPan(clampPan({x:d.pan.x+(e.clientX-d.x)/d.w*100,y:d.pan.y+(e.clientY-d.y)/d.h*100},zoom))}
 function end(){drag.current=null}
 function image(){
  const clip=overlayClip(position,zoom,pan.x);
  return <div className={'viewer-stage'+(compare?' comparison':'')+(movable?' movable':'')} style={{'--split':position+'%',touchAction:movable?'none':undefined}} onPointerDown={start} onPointerMove={move} onPointerUp={end} onPointerCancel={end} onDoubleClick={()=>{if(zoom>1)resetView()}}>
   <div className="viewer-image-wrap" style={{transform:`translate(${pan.x}%, ${pan.y}%) scale(${zoom})`}}>
    <img className="viewer-original" src={url(record.image_url)} alt="Inspected product original" draggable={false}/>
    {compare?<img className="viewer-overlay" style={{clipPath:`inset(0 0 0 ${clip}%)`}} src={url(record.heatmap_url)} alt="Measured anomaly heatmap comparison" draggable={false}/>:heatmap&&<img className="viewer-overlay full" src={url(record.heatmap_url)} alt="Measured anomaly localization heatmap" draggable={false}/>}
   </div>
   {compare&&<><div className="comparison-line"/><span className="viewer-label left">ORIGINAL</span><span className="viewer-label right">HIGHLIGHTED AREAS</span><input aria-label="Compare original and heatmap" className="comparison-range" type="range" min="0" max="100" value={position} onChange={e=>{setPosition(Number(e.target.value));onComparisonUsed?.()}}/></>}
  </div>;
 }
 const help=compare?'Drag the divider to compare the photo and the highlighted areas.':movable?'Drag the photo to move around. Double-click to reset.':'Use Compare images to see both side by side.';
 return <><div className="viewer-controls"><button className={'secondary '+(compare?'selected':'')} aria-pressed={compare} onClick={()=>setCompare(!compare)}><SplitSquareHorizontal size={16}/>{compare?'Single image':'Compare images'}</button><div><button className="icon-button" aria-label="Zoom out" disabled={zoom<=ZOOM_MIN} onClick={()=>changeZoom(-1)}><ZoomOut size={17}/></button><button type="button" className="zoom-level" aria-label="Reset zoom" title="Reset zoom" disabled={zoom===1} onClick={resetView}>{Math.round(zoom*100)}%</button><button className="icon-button" aria-label="Zoom in" disabled={zoom>=ZOOM_MAX} onClick={()=>changeZoom(1)}><ZoomIn size={17}/></button><button className="icon-button" aria-label="Expand inspection image" onClick={()=>setExpanded(true)}><Expand size={17}/></button></div></div>{image()}<p className="caption">{help} Highlighted areas look different from normal examples. Stronger colors do not mean a more serious defect.</p><dialog aria-label="Expanded inspection image" className="image-dialog" ref={dialog} onClose={()=>setExpanded(false)} onCancel={()=>setExpanded(false)}><div className="section-title"><h2>Inspection image · {record.id.slice(0,8)}</h2><button className="icon-button" aria-label="Close expanded image" onClick={()=>setExpanded(false)}><X size={20}/></button></div>{expanded&&image()}</dialog></>;
}
