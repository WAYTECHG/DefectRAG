import React,{useEffect,useState} from 'react';
import {pickReferences,rankLabel,referenceUrl} from './references.mjs';

// One small file per product, fetched once and kept for the session.
const libraries=new Map();
const load=category=>{
  if(!libraries.has(category))libraries.set(category,fetch(referenceUrl(category)).then(r=>r.ok?r.json():null).catch(()=>null));
  return libraries.get(category);
};

export default function ReferencePhotos({record}){
  const [library,setLibrary]=useState(null);
  const wanted=Boolean(record?.references?.length);
  useEffect(()=>{
    let current=true;
    setLibrary(null);
    if(wanted)load(record.category).then(value=>{if(current)setLibrary(value)});
    return()=>{current=false};
  },[record?.id,record?.category,wanted]);
  const items=pickReferences(record,library);
  if(!items.length)return null;
  return <section className="references" aria-label="Closest normal reference photos">
    <h3>Closest normal reference photos</h3>
    <p className="caption">Normal training photos of this product that look most like the photo above. They are for comparison only and do not change the result.</p>
    <div className="reference-row">{items.map((item,index)=><figure key={item.id}><img src={item.thumb} alt={`Normal reference photo ${item.id}`} loading="lazy"/><figcaption>{rankLabel(index)}</figcaption></figure>)}</div>
    {library?.attribution&&<p className="caption">{library.attribution}</p>}
  </section>;
}
