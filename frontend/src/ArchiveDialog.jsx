import React,{useEffect,useRef} from 'react';
import {Archive,X} from 'lucide-react';
export default function ArchiveDialog({open,onClose,onConfirm,busy}){
 const dialog=useRef(null);
 useEffect(()=>{if(open)dialog.current?.showModal();else dialog.current?.close()},[open]);
 return <dialog ref={dialog} className="confirmation-dialog" onCancel={onClose} onClose={onClose}><div className="section-title"><div className="setup-icon"><Archive size={25}/></div><button className="icon-button" aria-label="Cancel clear history" disabled={busy} onClick={onClose}><X size={18}/></button></div><h2>Clear this view, keep the evidence.</h2><p>All local inspections matching your current history filters will be archived, including matches beyond the first 500 displayed rows. They will disappear from the active history and review queue.</p><div className="note">Images, measurements and conversations are preserved. You can restore them in History recovery. This action does not change cloud records.</div><div className="button-row"><button className="secondary" onClick={onClose} disabled={busy}>Keep history</button><button className="primary" onClick={onConfirm} disabled={busy}>{busy?'Archiving…':'Archive matching history'}</button></div></dialog>;
}
