import pg from './node_modules/.pnpm/pg@8.18.0/node_modules/pg/lib/index.js';
const { Client } = pg;
const c = new Client({host:'127.0.0.1',port:54329,user:'paperclip',password:'paperclip',database:'paperclip'});
await c.connect();
const r1 = await c.query("SELECT column_name FROM information_schema.columns WHERE table_name='agent_runtime_state'");
console.log('cols:', r1.rows.map(row=>row.column_name).join(', '));
const r2 = await c.query("SELECT * FROM agent_runtime_state WHERE agent_id = 'baf2b0ba-52e7-4844-8f96-fbcc32c10d95'");
console.log('row:', JSON.stringify(r2.rows[0], null, 2));
await c.end();

// Reset session
const r3 = await c.connect().then ? null : null;
