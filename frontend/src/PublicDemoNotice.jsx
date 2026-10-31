import React from 'react';
// One demo banner: replaces the separate workspace status note on demo pages.
export default function PublicDemoNotice({cloud,onStart,status}){
 return <section className="note" role="status"><div className="demo-banner">
  <div><strong>Demo workspace · try the app without signing in</strong>
  <p className="caption">{cloud?'Demo results belong to this browser session and may disappear when the online app restarts. Private Staff records are not shown. Free service limits may cause a wait.':'Without signing in, results stay on this computer. They are separate from account and Team records.'} Sign in with an approved account to keep private work across devices.{status&&<> {status}</>}</p></div>
  {onStart&&<button className="secondary" onClick={onStart}>Try an inspection</button>}
 </div></section>;
}
