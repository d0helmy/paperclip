import pg from './node_modules/.pnpm/pg@8.18.0/node_modules/pg/lib/index.js';
const { Client } = pg;
const c = new Client({host:'127.0.0.1',port:54329,user:'paperclip',password:'paperclip',database:'paperclip'});
await c.connect();
const r = await c.query("SELECT id, name, adapter_config FROM agents WHERE id = 'baf2b0ba-52e7-4844-8f96-fbcc32c10d95'");
console.log('agent:', JSON.stringify(r.rows[0], null, 2));
await c.end();
