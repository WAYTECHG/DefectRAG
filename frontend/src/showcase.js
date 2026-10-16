// A read-only adapter for the explicitly labelled public showcase.
export const SHOWCASE = import.meta.env.MODE === 'showcase';
let snapshot;
export const assetUrl = path => {
  if (!SHOWCASE) return (import.meta.env.VITE_API_URL || '').replace(/\/$/, '') + path;
  if (path === '/api/export.csv') return './showcase/inspections.csv';
  const report = path.match(/^\/api\/inspections\/([a-f0-9]{32})\/report$/);
  return report ? `./showcase/reports/${report[1]}.html` : path;
};
export async function showcaseApi(path, options = {}) {
  if ((options.method || 'GET') !== 'GET') throw new Error('Saved showcase: run the local application for live inspection, questions and alert updates.');
  snapshot ||= fetch('./showcase/data.json', {cache:'no-store'}).then(response => {
    if (!response.ok) throw new Error('Saved examples could not be loaded. Refresh or try again later.');
    return response.json();
  }).catch(error => { snapshot = null; throw error; });
  const data = await snapshot;
  const route = path.split('?')[0];
  if (route === '/api/benchmark/official') return data.official_evaluation || {categories:{},status:'not_run'};
  if (route === '/api/archives') return [];
  if (route === '/api/health') return {status: 'ok', mode: 'saved_examples'};
  if (route === '/api/evaluation') return data.evaluation;
  if (route === '/api/samples') return data.samples;
  if (route === '/api/inspections') return data.records;
  if (route === '/api/alerts') return data.records.filter(r => r.verdict !== 'Good').map(r => ({id:r.id, inspection_id:r.id, kind:r.verdict, created_at:r.created_at, acknowledged:0}));
  if (route === '/api/stats') return {total:data.records.length, counts:data.records.reduce((counts,r) => ({...counts,[r.verdict]:(counts[r.verdict]||0)+1}),{}), batches:[{batch:'Verified VisA examples'}]};
  const match = route.match(/^\/api\/inspections\/([a-f0-9]{32})(\/messages)?$/);
  if (match) {
    const record = data.records.find(r => r.id === match[1]);
    if (!record) throw new Error('Saved example not found.');
    return match[2] ? data.messages[match[1]] || [] : record;
  }
  throw new Error('This action needs the local application.');
}
