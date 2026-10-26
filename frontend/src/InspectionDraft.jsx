import React from 'react';

export default function InspectionDraft({multiple,files=[]}){
 return <div className="caption" role="status">
  <p>{multiple?'Check up to 20 photos together. Choose a new batch name to keep their results together. Photos do not need to be inspected first. This page checks uploaded photos, not a live camera.':'Check one product photo, see any unusual areas highlighted, and ask questions about the result.'}</p>
  {files.length>0&&<p><strong>{files.length} selected photo{files.length===1?'':'s'} ready to inspect.</strong> Choose Run inspection or Inspect batch to get a result. A filename does not tell whether the same photo was checked before.</p>}
 </div>;
}
