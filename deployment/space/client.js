import {Client} from '@gradio/client';
export {Client};
export function closeClient(client){
  // predict() resolves on process_completed, before the SSE reader necessarily
  // finishes. An intentional abort is normal disposal, not a failed model job.
  const stream=client.stream_instance;
  if(stream){
    const onerror=stream.onerror;
    stream.onerror=error=>{if(error?.name!=='AbortError')onerror?.(error)};
  }
  client.close();
}
