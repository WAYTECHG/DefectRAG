import {Client} from '@gradio/client';

let connection;
export async function phase1Fetch(path, options={}) {
  if (new URL(path, location.origin).pathname !== '/api/inspect' || options.method !== 'POST') {
    return fetch(path, options);
  }
  try {
    connection ||= Client.connect(location.origin);
    const client = await connection;
    const body = options.body;
    const file = body.get('file');
    const image_b64 = await new Promise((resolve,reject)=>{
      const reader = new FileReader();
      reader.onload=()=>resolve(String(reader.result).split(',')[1]);
      reader.onerror=()=>reject(new Error('Image could not be read'));
      reader.readAsDataURL(file);
    });
    const output = await client.predict('/inspect', {image_b64, filename:file.name,
      category:body.get('category'), batch:body.get('batch')||''});
    return new Response(JSON.stringify({data:output.data[0]}), {status:200,headers:{'Content-Type':'application/json'}});
  } catch(error) {
    connection=undefined;
    return new Response(JSON.stringify({error:{message:error.message||'Gradio request failed'}}),
      {status:503,headers:{'Content-Type':'application/json'}});
  }
}
