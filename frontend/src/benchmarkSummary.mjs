// Before/after headline for the Official benchmark page. "Before" is the frozen
// DINOv2 baseline from the official report (three seeds); "after" is the deployed
// fine-tuned profile from /api/evaluation (one run, same official test split).
const number=value=>typeof value==='number'&&Number.isFinite(value)?value:null;

export function deployedSummary(evaluation,baseline){
 const after=evaluation?.macro_mean;
 if(evaluation?.profile!=='dinov2_tuned_v1'||number(after?.image_auroc)===null)return null;
 const before=baseline?.macro_mean||{};
 return {
  profile:evaluation.profile,
  cards:[
   {key:'image_auroc',label:'Mean image AUROC',after:number(after.image_auroc),before:number(before.auroc)},
   {key:'recall',label:'Defects caught',after:number(after.recall),before:null},
   {key:'false_positive_rate',label:'Normal photos flagged',after:number(after.false_positive_rate),before:null},
   {key:'pixel_auroc',label:'Mean pixel AUROC',after:number(after.pixel_auroc_224),before:number(before.pixel_auroc)}
  ]
 };
}
