import React from 'react';
import {TriangleAlert,RotateCcw,LayoutDashboard,Copy} from 'lucide-react';
import {recordIssue,diagnosticReport} from './diagnostics.mjs';

// One broken page must never blank the whole app. The rest of the app keeps
// working, the problem is recorded for "Copy details", and changing page resets it.
export default class ErrorBoundary extends React.Component{
 constructor(props){super(props);this.state={error:null,copied:false}}
 static getDerivedStateFromError(error){return {error}}
 componentDidCatch(error,info){recordIssue('screen',(error?.message||String(error))+' '+String(info?.componentStack||'').trim().split('\n')[0],{path:this.props.resetKey})}
 componentDidUpdate(previous){if(previous.resetKey!==this.props.resetKey&&this.state.error)this.setState({error:null,copied:false})}
 async copy(){
  try{await navigator.clipboard.writeText(diagnosticReport(this.props.context?.()||{}));this.setState({copied:true})}catch{this.setState({copied:false})}
 }
 render(){
  if(!this.state.error)return this.props.children;
  return <section className="card crash-card" role="alert">
   <div className="crash-icon"><TriangleAlert size={28}/></div>
   <h2>This page could not be shown</h2>
   <p>Your saved work is safe. Try the page again, or go back to the overview.</p>
   <div className="button-row">
    <button type="button" className="primary" onClick={()=>this.setState({error:null,copied:false})}><RotateCcw size={17}/> Try again</button>
    <button type="button" className="secondary" onClick={()=>this.props.onHome?.()}><LayoutDashboard size={17}/> Go to Overview</button>
    <button type="button" className="secondary" onClick={()=>this.copy()}><Copy size={17}/> {this.state.copied?'Details copied':'Copy details for support'}</button>
   </div>
  </section>;
 }
}
