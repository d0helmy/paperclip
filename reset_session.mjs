import pg from './node_modules/.pnpm/pg@8.18.0/node_modules/pg/lib/index.js';
const { Client } = pg;
const c = new Client({host:'127.0.0.1',port:54329,user:'paperclip',password:'paperclip',database:'paperclip'});
await c.connect();
const r = await c.query(
  "UPDATE agent_runtime_state SET session_id = NULL WHERE agent_id = 'baf2b0ba-52e7-4844-8f96-fbcc32c10d95'"
);
console.log('Updated rows:', r.rowCount);
const r2 = await c.query("SELECT session_id FROM agent_runtime_state WHERE agent_id = 'baf2b0ba-52e7-4844-8f96-fbcc32c10d95'");
console.log('New session_id:', r2.rows[0].session_id);
await c.end();
