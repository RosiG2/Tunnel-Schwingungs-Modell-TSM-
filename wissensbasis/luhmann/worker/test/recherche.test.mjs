import {readFileSync,readdirSync} from 'node:fs';
import {join,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
import test from 'node:test';
import {searchCorpus,getReferencePath} from '../src/recherche.ts';
const dir=dirname(fileURLToPath(import.meta.url));
const idx=JSON.parse(readFileSync(join(dir,'../../index.json'),'utf-8'));
const corpus=new Map(idx.entries.map(e=>[e.id,readFileSync(join(dir,'../../entries',e.id+'.md'),'utf-8')]));

test('all 17 article IDs have files and links only refer to known IDs',()=>{
 assert.equal(idx.entries.length,17);
 assert.equal(readdirSync(join(dir,'../../entries')).filter(s=>s.endsWith('.md')).length,17);
 const ids=new Set(idx.entries.map(e=>e.id));
 for(const e of idx.entries)for(const related of e.related_ids||[])assert(ids.has(related));
});
test('subject query finds the actual school reform case',()=>{
 const v=searchCorpus(idx,corpus,'Schulreform und Lernklima',8);
 assert.equal(v.edition,'atlas-0.3-redaktion');
 assert.equal(v.incomplete,false);
 assert(v.results.some(e=>e.id==='schulreform-und-lernklima'));
 assert(v.results.every(e=>e.score>0));
});
test('communication and AI query finds matching registered articles',()=>{
 const v=searchCorpus(idx,corpus,'Mensch KI Kommunikation',10);
 assert(v.results.some(e=>e.id==='mensch-ki-kommunikation'));
 assert(v.results.every(x=>idx.entries.some(e=>e.id===x.id)));
});
test('graph returns exact editorial links with no hallucinated nodes',()=>{
 const v=getReferencePath(idx,'strukturelle-kopplung',1);
 assert(v.nodes.some(e=>e.id==='politik-recht-konflikt'));
 assert(v.nodes.some(e=>e.id==='operative-geschlossenheit'));
 assert(v.edges.every(x=>idx.entries.find(e=>e.id===x.from).related_ids?.includes(x.to)));
});
test('unknown IDs cannot return a graph',()=>{
 assert.equal(getReferencePath(idx,'geheime-archivakte-2030'),null);
});
test('no matches return empty results without fabrication',()=>{
 const v=searchCorpus(idx,corpus,'xyzabcnonexistentterm',8);
 assert.equal(v.results.length,0);
});
test('missing articles mark incomplete search rather than claiming complete coverage',()=>{
 const partial=new Map([...corpus].slice(0,10));
 const v=searchCorpus(idx,partial,'System und Umwelt');
 assert.equal(v.incomplete,true);assert.equal(v.scanned,10);
});

test('transliteration permits German umlaut and ASCII spelling',()=>{
 const a=searchCorpus(idx,corpus,'strukturelle Kopplung',10);
 assert(a.results.some(r=>r.id==='strukturelle-kopplung'));
 const u=searchCorpus(idx,corpus,'Verstaendigung',10);
 assert(u.results.some(r=>r.id==='kommunikation-und-verstehen'||r.id==='autopoiesis'));
});
test('excerpts actually contain at least one query term when present',()=>{
 const a=searchCorpus(idx,corpus,'Schulreform Lernklima',10);
 for(const item of a.results.filter(r=>r.excerpt)){
  const fold=s=>s.replace(/ä/g,'ae').replace(/ö/g,'oe').replace(/ü/g,'ue').replace(/ß/g,'ss').toLowerCase();
  assert(['schulreform','lernklima'].some(w=>fold(item.excerpt).includes(w)));
  assert.equal(item.excerpt_source,'article_text');
 }
});
test('two-step graph keeps edges inside returned node set and respects bounds',()=>{
 const a=getReferencePath(idx,'system-und-umwelt',2,10);
 const ids=new Set(a.nodes.map(x=>x.id));
 assert(a.nodes.length<=10);
 assert(a.edges.every(e=>ids.has(e.from)&&ids.has(e.to)));
 assert.equal(a.depth,2);
});
test('stopword-only query is not misrepresented as corpus unavailability',()=>{
 const a=searchCorpus(idx,corpus,'und die',6);
 assert.equal(a.results.length,0);
 assert.equal(a.scanned,17);
 assert.equal(a.incomplete,false);
});
