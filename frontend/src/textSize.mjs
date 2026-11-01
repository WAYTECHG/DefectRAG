// Text size preference. The page is drawn at 100%; the default on a desktop screen is 80%
// (the size the owner found most comfortable). A saved choice always wins.
export const TEXT_SIZE_KEY='defectrag-text-size';
export const TEXT_SIZES=[0.8,0.9,1,1.15];
const valid=value=>TEXT_SIZES.includes(value);
export function initialTextSize(storage=globalThis.localStorage,width=globalThis.innerWidth){
 try{const saved=Number(storage?.getItem(TEXT_SIZE_KEY));if(valid(saved))return saved}catch{}
 return width>=900?0.8:1;
}
export function applyTextSize(size,root=globalThis.document?.documentElement,storage=globalThis.localStorage){
 const value=valid(size)?size:1;
 if(root)root.style.zoom=value===1?'':String(value);
 try{storage?.setItem(TEXT_SIZE_KEY,String(value))}catch{}
 return value;
}
export function stepTextSize(size,direction){
 const index=Math.max(0,TEXT_SIZES.indexOf(size));
 return TEXT_SIZES[Math.min(TEXT_SIZES.length-1,Math.max(0,index+(direction<0?-1:1)))];
}
