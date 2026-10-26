// LOCAL SIMULATION ONLY. No Supabase client, secrets, SMTP relay or outbound fetch.
// Run inside the existing n8n container so both listeners stay on its loopback.
import http from 'node:http';
import net from 'node:net';
import {pathToFileURL} from 'node:url';

export const fixtureEvent = Object.freeze({
  event_id: '11111111-1111-4111-8111-111111111111',
  lease_token: '22222222-2222-4222-8222-222222222222',
  case_id: '33333333-3333-4333-8333-333333333333', kind: 'created', version: 1,
});
export const fixtureMarker = 'public-local-simulation-only'; // Public marker, NOT a secret.
export const fixtureRecipient = 'supervisor@example.invalid';

export function createLedger() {
  let effect = 'new';
  let accepted = 0;
  let beginCalls = 0;
  let finishCalls = 0;
  let failFinish = false;
  let failSmtp = false;
  const mail = [];
  return {
    status: () => ({mode: 'LOCAL SIMULATION ONLY', effect, accepted, beginCalls,
      finishCalls, realEmailsSent: 0, failFinish, failSmtp, mail: [...mail]}),
    configure(b) {
      if (Object.keys(b).some(k => !['failFinish', 'failSmtp'].includes(k)) ||
          Object.values(b).some(v => typeof v !== 'boolean')) return false;
      if ('failFinish' in b) failFinish = b.failFinish;
      if ('failSmtp' in b) failSmtp = b.failSmtp;
      return true;
    },
    request(marker, b) {
      if (marker !== fixtureMarker || !b || b.event_id !== fixtureEvent.event_id ||
          b.lease_token !== fixtureEvent.lease_token) return {status: 403, body: {error: 'fixture_only'}};
      if (b.operation === 'begin') {
        beginCalls++;
        if (effect === 'done') return {status: 200, body: {execute: false, done: true}};
        if (effect !== 'new') return {status: 200, body: {execute: false, done: false, manual_review: true}};
        effect = 'processing';
        return {status: 200, body: {execute: true, done: false, recipient_email: fixtureRecipient,
          case_id: fixtureEvent.case_id, kind: 'created', state: 'Open', priority: 'High',
          due_at: '2030-01-01T00:00:00Z'}};
      }
      if (b.operation === 'finish') {
        finishCalls++;
        if (failFinish) return {status: 503, body: {error: 'simulated_receipt_failure'}};
        if (effect !== 'processing' || accepted !== 1 || typeof b.receipt !== 'string' ||
            !b.receipt || b.receipt.length > 200) return {status: 409, body: {error: 'fixture_receipt_not_accepted'}};
        effect = 'done';
        return {status: 200, body: {done: true}};
      }
      return {status: 400, body: {error: 'invalid_operation'}};
    },
    canAccept: () => !failSmtp && effect === 'processing' && accepted === 0,
    accept() {
      if (!this.canAccept()) return false;
      accepted++;
      mail.push({to: fixtureRecipient, from: 'fixture@example.invalid',
        subject: 'DefectRAG corrective action notification', transport: 'local sink; no relay'});
      return true;
    },
  };
}

export async function startFixture({httpPort = 18081, smtpPort = 12525, lifetimeMs = 1800000} = {}) {
  const ledger = createLedger();
  const sockets = new Set();
  const server = http.createServer(async (req, res) => {
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Cache-Control', 'no-store');
    const send = (status, body) => {res.writeHead(status); res.end(JSON.stringify(body));};
    if (req.method === 'GET' && req.url === '/qa/status') {
      send(200, {...ledger.status(), processId: process.pid, bound: '127.0.0.1 inside n8n container'}); return;
    }
    if (req.method !== 'POST' || !['/effect', '/qa/control'].includes(req.url)) {
      send(404, {error: 'local_fixture_route_only'}); return;
    }
    if (req.headers['x-defectrag-local-qa'] !== fixtureMarker) {send(403, {error: 'fixture_only'}); return;}
    let size = 0;
    const chunks = [];
    try {
      for await (const c of req) {
        size += c.length;
        if (size > 4096) {send(413, {error: 'fixture_body_limit'}); return;}
        chunks.push(c);
      }
      const b = JSON.parse(Buffer.concat(chunks).toString('utf8'));
      if (!b || Array.isArray(b) || typeof b !== 'object') {send(400, {error: 'invalid_json_object'}); return;}
      if (req.url === '/qa/control') {
        send(ledger.configure(b) ? 200 : 400, {mode: 'LOCAL SIMULATION ONLY'}); return;
      }
      const result = ledger.request(req.headers['x-defectrag-local-qa'], b);
      send(result.status, result.body);
    } catch {if (!res.writableEnded) send(400, {error: 'invalid_fixture_input'});}
  });
  server.requestTimeout = 5000;
  server.headersTimeout = 5000;
  const smtp = net.createServer(socket => {
    sockets.add(socket);
    socket.on('close', () => sockets.delete(socket));
    socket.on('error', () => {});
    socket.setTimeout(10000, () => socket.destroy());
    socket.write('220 local-practice.invalid ESMTP sink-only\r\n');
    let buffer = '', data = false, sender = false, recipient = false, bytes = 0;
    socket.on('data', chunk => {
      bytes += chunk.length;
      if (bytes > 65536) {socket.destroy(); return;}
      buffer += chunk.toString('utf8');
      for (;;) {
        const index = buffer.indexOf('\r\n');
        if (index < 0) break;
        const line = buffer.slice(0, index); buffer = buffer.slice(index + 2);
        if (data) {
          if (line === '.') {data = false; socket.write(ledger.accept() ? '250 2.0.0 accepted by LOCAL sink\r\n' : '550 local sink refused\r\n');}
          continue; // Discard content, never relay or save raw messages.
        }
        if (/^(EHLO|HELO)\b/i.test(line)) socket.write('250-local-practice.invalid\r\n250 SIZE 65536\r\n');
        else if (/^MAIL FROM:<fixture@example\.invalid>/i.test(line)) {sender = true; recipient = false; socket.write('250 OK\r\n');}
        else if (/^RCPT TO:<supervisor@example\.invalid>/i.test(line) && sender && ledger.canAccept()) {recipient = true; socket.write('250 OK\r\n');}
        else if (/^MAIL FROM:|^RCPT TO:/i.test(line)) socket.write('550 Only fixed synthetic envelope allowed\r\n');
        else if (line === 'DATA' && sender && recipient) {data = true; socket.write('354 End with dot\r\n');}
        else if (line === 'QUIT') socket.end('221 bye\r\n');
        else if (line === 'RSET') {sender = false; recipient = false; socket.write('250 OK\r\n');}
        else socket.write('500 Unsupported local command\r\n');
      }
    });
  });
  try {
    await new Promise((resolve, reject) => {server.once('error', reject); server.listen(httpPort, '127.0.0.1', resolve);});
    await new Promise((resolve, reject) => {smtp.once('error', reject); smtp.listen(smtpPort, '127.0.0.1', resolve);});
  } catch (e) {server.close(); smtp.close(); throw e;}
  const close = () => {clearTimeout(timer); for (const s of sockets) s.destroy(); server.close(); smtp.close();};
  const timer = setTimeout(close, lifetimeMs);
  return {ledger, close, httpPort: server.address().port, smtpPort: smtp.address().port};
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (process.env.DEFECTRAG_LOCAL_PRACTICE !== '1') throw Error('Explicit local practice flag required');
  const fixture = await startFixture();
  console.log(JSON.stringify({mode: 'LOCAL SIMULATION ONLY', bound: '127.0.0.1 inside n8n container',
    httpPort: fixture.httpPort, smtpPort: fixture.smtpPort, expiresMinutes: 30}));
  process.once('SIGTERM', fixture.close); process.once('SIGINT', fixture.close);
}
