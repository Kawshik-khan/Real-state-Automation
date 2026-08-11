const fs = require('fs');
const http = require('http');

// Step 1: Read the JSON file
const raw = fs.readFileSync('C:/Users/Kawshik Khan/AppData/Local/Temp/n8n-import-clean.json', 'utf8');
const data = JSON.parse(raw);
const wf = Array.isArray(data) ? data[0] : data;

// Step 2: Strip server-managed fields
delete wf.id;
delete wf.active;
delete wf.versionId;
delete wf.activeVersionId;
delete wf.shared;
delete wf.createdAt;
delete wf.updatedAt;
delete wf.checksum;
delete wf.versionCounter;
delete wf.ownedBy;
delete wf.sharedWith;

// Step 3: Save fixed version
const fixedPath = 'C:/Users/Kawshik Khan/AppData/Local/Temp/n8n-single-workflow.json';
fs.writeFileSync(fixedPath, JSON.stringify(wf, null, 2));
console.log(`Fixed workflow written to ${fixedPath}`);
console.log(`Workflow: "${wf.name}"`);
console.log(`Nodes: ${wf.nodes.length}`);
console.log('Server-managed fields stripped.');
console.log('Ready for REST API import.');
