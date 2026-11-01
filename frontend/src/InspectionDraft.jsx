import React from 'react';

export default function InspectionDraft({multiple,files=[]}){
 return <div className="caption" role="status">
  <p>{multiple?'Check up to 20 photos at once. Give the batch a new name so its results stay together.':'Check one product photo. Unusual areas are highlighted, and you can ask about the result.'}</p>
  {(multiple?files.length>0:files.length===1)&&<p><strong>{files.length} photo{files.length===1?'':'s'} ready.</strong> Press {multiple?'Inspect batch':'Run inspection'} to get the result.</p>}
 </div>;
}
