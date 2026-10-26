import React from 'react';
export default function PublicDemoNotice({cloud,onStart}){
 return <section className="note" role="status"><div>
  <strong>Try the app without signing in</strong>
  <p>Choose a sample photo or upload a photo of a supported product. Sign in with an approved account to keep private work across devices.</p>
  <p className="caption">{cloud?'Demo results belong to this browser session and may disappear when the online app restarts. Private Staff records are not shown. Free service limits may cause a wait.':'Without signing in, results stay on this computer. They are separate from account and Team records.'}</p>
  <button className="secondary" onClick={onStart}>Try an inspection</button>
 </div></section>;
}
