#!/usr/bin/env node
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const pg = require('/Users/dia/paperclip/node_modules/.pnpm/pg@8.18.0/node_modules/pg');
const { Client } = pg;
const c = new Client({host:'127.0.0.1',port:54329,user:'paperclip',password:'paperclip',database:'paperclip'});
await c.connect();

// Check ALL lines of the latest run LOG (not just result_json)
const r = await c.query(`
  SELECT result_json, log_ref
  FROM heartbeat_runs
  WHERE agent_id = 'baf2b0ba-52e7-4844-8f96-fbcc32c10d95'
  ORDER BY created_at DESC LIMIT 1
`);
if (r.rows.length === 0) { console.log('no runs'); } else {
  const row = r.rows[0];
  const rjStr = typeof row.result_json === 'string' ? row.result_json : JSON.stringify(row.result_json);
  const rj = JSON.parse(rjStr);
  const stdout = rj.stdout || '';
  console.log('=== FULL STDOUT ===');
  console.log(stdout);
}

await c.end();
