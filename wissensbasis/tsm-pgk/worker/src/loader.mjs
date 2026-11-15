/* Publication loader: GitHub branch -> one immutable commit -> hash verified bundle.
 * A single GitHub commit is selected per request. The explicitly supplied revision
 * can be used across research calls when the researcher wants fixed provenance.
 */
import {createPublicResearchApi} from './public_core.mjs';
export const DEFAULT_REPO='RosiG2/Tunnel-Schwingungs-Modell-TSM-';
const prefix='wissensbasis/tsm-pgk/';
const commitPattern=/^[a-f0-9]{40}$/i;
const bytes=x=>new TextEncoder().encode(x);
export async function sha256Bytes(input){const buf=input instanceof Uint8Array?input:bytes(input);const digest=await crypto.subtle.digest('SHA-256',buf);return Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,'0')).join('');}
function integrityError(s){const e=new Error(s);e.kind='INTEGRITY_ERROR';return e;}
export async function verifyPublication(bundleText,manifestText,{full=true,allowPreview=false}={}){
  const manifest=JSON.parse(manifestText),bundle=JSON.parse(bundleText);
  if(manifest.schema!=='pgk.mcp.public-manifest.v1'||bundle.schema!=='pgk.mcp.public-essence.v1')
    throw integrityError('Wrong public-only publication schema');
  if(await sha256Bytes(bundleText)!==manifest.bundle_sha256)
    throw integrityError('Immutable bundle SHA-256 mismatch');
  const paths=Object.keys(bundle.files);
  if(paths.length!==manifest.files_count)throw integrityError('Unexpected public file count');
  for(const p of paths){
    if(p.includes('..')||p.startsWith('/')||p.startsWith('INTERN')||p.startsWith('mcp/'))throw integrityError('Forbidden public file path '+p);
    const f=bundle.files[p];
    if(manifest.file_sha256[p]!==f.sha256)throw integrityError('Manifest/file digest mapping mismatch: '+p);
    if(typeof f.content!=='string')throw integrityError('Content missing: '+p);
    if(full && (bytes(f.content).length!==f.bytes || await sha256Bytes(f.content)!==f.sha256))
      throw integrityError('Public source content hash mismatch: '+p);
  }
  for(const key of ['daten/module.json','daten/claims.json','daten/relations.json',
     'daten/sources.json','daten/research_findings.json','daten/research_state.json',
     'erscheinungswelt/daten/vergleich_kandidaten_v02.json','erscheinungswelt/daten/ew_anker_v02.json',
     'erscheinungswelt/daten/modell_luecken_v02.json','erscheinungswelt/daten/erganzende_forschungsfronten_v02.json'])
    if(!bundle.files[key])throw integrityError('Required public component missing: '+key);
  const mods=JSON.parse(bundle.files['daten/module.json'].content).modules;
  const claims=JSON.parse(bundle.files['daten/claims.json'].content).claims;
  const rels=JSON.parse(bundle.files['daten/relations.json'].content).relations;
  if(mods.length!==manifest.counts.modules||claims.length!==manifest.counts.claims||rels.length!==manifest.counts.relations)
    throw integrityError('Public inventory count mismatch');
  if(JSON.parse(bundle.files['erscheinungswelt/daten/vergleich_kandidaten_v02.json'].content).item_count!==590 ||
     JSON.parse(bundle.files['erscheinungswelt/daten/ew_anker_v02.json'].content).anchor_count!==16 ||
     JSON.parse(bundle.files['erscheinungswelt/daten/modell_luecken_v02.json'].content).count!==20)
    throw integrityError('Exploratory research inventory mismatch');
  if(manifest.publication_approved!==bundle.publication_approved)
    throw integrityError('Release authorization flags differ');
  if(bundle.publication_approved!==true && !allowPreview)
    throw integrityError('Unapproved public research preview cannot be served in production');
  for(const name of ['research_findings','evidence_passports','review_relations']){
    const p='daten/'+name+'.json';
    if(bundle.files[p]){
      const d=JSON.parse(bundle.files[p].content);
      const rows=d.findings||d.passports||d.relations||[];
      for(const item of rows)if(item.public_research_memory!==true || item.public_record_scope!=='OPEN_RESEARCH_MEMORY')
        throw integrityError('Non-public or malformed research memory record in bundle: '+name);
    }
  }
  return {bundle,manifest,manifest_file_sha256:await sha256Bytes(manifestText),
    integrity_level:full?'FULL_PUBLIC_FILE_HASHES':'BUNDLE_DIGEST_AND_MANIFEST_CONSISTENCY'};
}
// Cache only immutable, revision-addressed publication bytes; never cache chat
// content, draft submissions or scientific answers. Local maps are isolate-local.
const branchCache=new Map(),publicationCache=new Map(),inflightPublications=new Map(),inflightBranches=new Map();
const BRANCH_TTL_MS=120000, PUBLICATION_TTL_MS=600000;
function repositoryFrom(env){
 const repo=env.GITHUB_REPOSITORY||DEFAULT_REPO;
 if(!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repo))throw Error('Invalid repository configuration');
 return repo;
}
function gitHeaders(env){let h={'Accept':'application/vnd.github+json','User-Agent':'TSM-PGK-readonly-MCP/0.8.1'};if(env.GITHUB_TOKEN)h.Authorization='Bearer '+env.GITHUB_TOKEN;return h;}
async function fetchChecked(url,headers={},maxBytes=6000000){
 let r=await fetch(url,{headers,redirect:'follow'});
 if(!r.ok)throw Error(`Upstream GitHub read failed (${r.status})`);
 const expected=Number(r.headers.get('Content-Length'));
 if(expected>maxBytes)throw Error('Publication upstream payload too large');
 const value=await r.text();
 if(bytes(value).length>maxBytes)throw Error('Publication upstream payload too large');
 return value;
}
function edgeCacheFor(env){
 if(String(env.PGK_EDGE_CACHE||'on').toLowerCase()==='off')return null;
 // Cloudflare Cache API is optional and local to a data center, not durable.
 return globalThis.caches?.default||null;
}
async function readEdgePair(cache,manifestUrl,bundleUrl){
 if(!cache)return null;
 try{
   const [m,b]=await Promise.all([cache.match(new Request(manifestUrl)),cache.match(new Request(bundleUrl))]);
   return m&&b?[await m.text(),await b.text()]:null;
 }catch{return null;}
}
async function cacheEdgePair(cache,manifestUrl,bundleUrl,manifestText,bundleText){
 if(!cache)return;
 const options={headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'public, max-age=43200'}};
 try{await Promise.all([
  cache.put(new Request(manifestUrl),new Response(manifestText,options)),
  cache.put(new Request(bundleUrl),new Response(bundleText,options))
 ]);}catch{/* Cache is best effort. GitHub and hashes remain the source of truth. */}
}
export async function resolveRevision(env){
 const fixed=env.PGK_FIXED_REVISION;
 if(fixed){if(!commitPattern.test(fixed))throw Error('Invalid PGK_FIXED_REVISION');return fixed.toLowerCase();}
 const repository=repositoryFrom(env), branch=env.GITHUB_BRANCH||'main';
 if(!/^[a-zA-Z0-9._/-]+$/.test(branch))throw Error('Invalid branch configuration');
 const key=repository+'#'+branch,old=branchCache.get(key);
 if(old&&Date.now()-old.time<BRANCH_TTL_MS)return old.sha;
 if(inflightBranches.has(key))return inflightBranches.get(key);
 const task=(async()=>{
   const u=`https://api.github.com/repos/${repository}/git/ref/heads/${branch}`;
   const r=JSON.parse(await fetchChecked(u,gitHeaders(env),100000));
   if(!commitPattern.test(r.object?.sha||''))throw Error('GitHub ref does not contain a commit SHA');
   const sha=r.object.sha.toLowerCase();branchCache.set(key,{sha,time:Date.now()});return sha;
 })();
 inflightBranches.set(key,task);
 try{return await task;}finally{inflightBranches.delete(key);}
}
export async function loadPublication(env,revision){
 if(!commitPattern.test(revision))throw Error('Only full 40-hex Git commit revisions can be requested');
 revision=revision.toLowerCase();
 const repository=repositoryFrom(env),key=repository+'#'+revision;
 const cached=publicationCache.get(key);if(cached&&Date.now()-cached.time<PUBLICATION_TTL_MS)return cached.value;
 if(inflightPublications.has(key))return inflightPublications.get(key);
 const task=(async()=>{
   const base=`https://raw.githubusercontent.com/${repository}/${revision}/${prefix}mcp/publication/`;
   const manifestUrl=base+'manifest.json',bundleUrl=base+'bundle.json';
   const edge=edgeCacheFor(env);
   const fromCache=await readEdgePair(edge,manifestUrl,bundleUrl);
   const [manifestText,bundleText]=fromCache||await Promise.all([
     fetchChecked(manifestUrl,{},1000000),fetchChecked(bundleUrl,{},6000000)
   ]);
   // Always verify: neither edge-cache presence nor a published hash grants
   // scientific validity. Invalid cached bytes fail closed, never silently used.
   // Build-time and regression tests independently verify all 105 source hashes.
   // At runtime the immutable bundle hash authenticates every byte at once;
   // repeating 105 individual SHA-256 hashes is costly on Free-tier CPU.
   const verified=await verifyPublication(bundleText,manifestText,{full:false,allowPreview:String(env.PGK_ALLOW_PREVIEW).toLowerCase()==='true'});
   if(!fromCache)await cacheEdgePair(edge,manifestUrl,bundleUrl,manifestText,bundleText);
   const value={...verified,revision,origin:'github-immutable-public-commit',integrity_checked:true};
   publicationCache.set(key,{time:Date.now(),value});
   if(publicationCache.size>3){for(const k of publicationCache.keys()){if(k!==key){publicationCache.delete(k);break;}}}
   return value;
 })();
 inflightPublications.set(key,task);
 try{return await task;}finally{inflightPublications.delete(key);}
}
export async function apiForRequest(env,requestedRevision=null){
 if(requestedRevision!=null&&!commitPattern.test(requestedRevision))throw Error('revision must be a full 40-hex commit SHA');
 const revision=requestedRevision||await resolveRevision(env);
 const pub=await loadPublication(env,revision);
 return {api:createPublicResearchApi(pub.bundle,{revision,manifest_sha256:pub.manifest_file_sha256,bundle_sha256:pub.manifest.bundle_sha256,origin:pub.origin,integrity_checked:true,integrity_level:pub.integrity_level}),publication:pub};
}
