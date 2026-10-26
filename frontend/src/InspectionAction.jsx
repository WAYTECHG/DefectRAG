import React from 'react';
import {ScanLine,LoaderCircle} from 'lucide-react';
import {teamInspectionGuidance} from './inspectionReadiness.mjs';

export default function InspectionAction({readiness,busy,multiple,onRun,onSwitch,switchDisabled=false}){
 return <>
  <button type="button" className="primary wide" disabled={readiness.disabled} aria-describedby={readiness.disabled?'inspection-run-reason':undefined} title={readiness.reason||undefined} onClick={onRun}>
   {busy?<LoaderCircle className="spin" size={18}/>:<ScanLine size={18}/>} {busy?'Inspecting image…':multiple?'Inspect batch':'Run inspection'}
  </button>
  {readiness.disabled&&<p id="inspection-run-reason" className="caption" role="status">{readiness.reason}</p>}
  {readiness.teamRestricted&&<>
   {readiness.code!=='team'&&<p className="caption">{teamInspectionGuidance}</p>}
   <button type="button" className="secondary wide" disabled={switchDisabled} onClick={onSwitch}>Switch to Personal Workspace</button>
  </>}
 </>;
}
