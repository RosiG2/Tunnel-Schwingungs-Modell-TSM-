/* TSM–PGK MCP v0.8.1 – read-only, source-faithful research API.
 * No research is created, approved, or written by this code.
 * Use a single verified publication bundle for each call.
 */
const DIRECTIONS = new Set(['both','incoming','outgoing']);
const MAX_PAGE = 50;
const DOC_MARK = 'Wissenschaftliche Beziehungen werden nur als einzeln dokumentierte Direktbeziehungen ausgegeben. Keine automatische transitive Implikation.';
function fail(message, kind='INVALID_ARGUMENT'){ const e=new Error(message);e.kind=kind; throw e; }
function obj(o){return o && typeof o==='object' && !Array.isArray(o) ? o : null;}
function limitOf(v, d=15,max=MAX_PAGE){let n = v==null?d:Number(v);if(!Number.isInteger(n)||n<1||n>max)fail(`limit must be between 1 and ${max}`);return n;}
function offsetOf(v){let n=v==null?0:Number(v);if(!Number.isInteger(n)||n<0||n>100000)fail('offset invalid');return n;}
function page(values,a){const offset=offsetOf(a.offset),limit=limitOf(a.limit);return {total:values.length,offset,limit,has_more:offset+limit<values.length,items:values.slice(offset,offset+limit)};}
function text(o){return String(o??'');}
function norm(s){return text(s).normalize('NFKC').toLocaleLowerCase('de-DE');}
// Retrieval scoring is deliberately lexical and transparent. TSM alone determines
// research relevance, grounded estimates and relationships. Longer technical query
// words must match; generic connective words must not flood the search results.
const STOP_WORDS=new Set('der die das den dem des ein eine einer eines und oder mit von vom fuer für zur zum bei auf über ueber unter aus durch nach vor dass diese dieser dieses sind sein sich als auch noch schon sowie welche welcher welches warum wie was wo wer nicht'.split(' ').filter(x=>x!=='nicht'));
function tokens(s){return [...new Set(norm(s).match(/[\p{L}\p{N}]+/gu)||[])].filter(x=>x.length>2&&!STOP_WORDS.has(x)).slice(0,24);}
function matchedTerm(hay,term){
  // Exact token first. For technical compounds only, accept contained long stems.
  const words=hay.match(/[\p{L}\p{N}]+/gu)||[];
  return words.includes(term) || (term.length>=8 && words.some(w=>w.includes(term)));
}
function scoreField(value,q,kind='body'){
  const n=norm(value),qq=norm(q).trim(),parts=tokens(q);
  if(!qq)return 1;
  if(!parts.length)return 0;
  const significant=parts.filter(x=>x.length>=7);
  if(significant.length && !significant.some(t=>matchedTerm(n,t)))return 0;
  let nmatch=0,points=0;
  for(const term of parts){if(matchedTerm(n,term)){nmatch++;points+=term.length>=7?4:2;}}
  if(!nmatch)return 0;
  if(n.includes(qq))points+=(kind==='title'?35:16);
  if(nmatch===parts.length)points+=8;
  if(kind==='title')points*=3;
  return points;
}
function score(s,q){return scoreField(s,q);}
function searchScore(record,q){
  if(!q.trim())return 1;
  const body=scoreField(record.body,q),title=scoreField(record.title,q,'title');
  const id=norm(record.id),query=norm(q).trim();
  const idMatch=id===query?100:(id.startsWith(query)&&query.length>=4?25:0);
  if(!body&&!title&&!idMatch)return 0;
  return body+title+idMatch;
}
function edge(e){const o=e.eintrag||e; return {id:o.id,from:o.von??o.from_claim,to:o.nach??o.to_claim,type:o.relation??o.relation_type,record:e};}
function listPaths(bundle,prefix){return Object.keys(bundle.files).filter(p=>p.startsWith(prefix)).sort();}
function file(bundle,path){const o=bundle.files[path];if(!o)fail(`File not in approved public bundle: ${path}`,'NOT_FOUND');return o;}
function json(bundle,path){return JSON.parse(file(bundle,path).content);}
function view(src,spec,provenance){return {...src,...spec,provenance};}
function available(src){return src.mcp_fulltext_available===true;}
function msg(data){return {content:[{type:'text',text:JSON.stringify(data)}],structuredContent:data};}
function makeBaseline(bundle){const m=json(bundle,'META-PGK-01.json'), ew=json(bundle,'erscheinungswelt/META-EW-01.json'),br=json(bundle,'bruecken/META-PGK-EW-01.json');
// This compact signature is a stable source-oriented comparator; differences in objects are compared by JSON values.
const keyed=(rows,key)=>Object.fromEntries(rows.map(x=>[key(x),x]));
const documents=Object.fromEntries(Object.entries(bundle.files).filter(([path])=>path.startsWith('forschung/')&&path.endsWith('.md')).map(([path,file])=>[path,{path,sha256:file.sha256}]));
const axes=keyed([...(m.achsenkatalog.erkenntnisbereiche||[]),...(m.achsenkatalog.spiegelachsen||[])],x=>x.id);
return {modules:keyed(m.modules,x=>x.id),claims:keyed(m.claims,x=>x.id),relations:keyed(m.relations,x=>x.eintrag.id),sources:keyed(m.sources,x=>x.id),appearance:keyed(ew.records,x=>x.id),bridges:keyed(br.records,x=>x.id),documents,axes};
}
function stableJSON(x){if(Array.isArray(x))return "["+x.map(stableJSON).join(",")+"]";if(x&&typeof x==="object")return "{"+Object.keys(x).sort().map(k=>JSON.stringify(k)+":"+stableJSON(x[k])).join(",")+"}";return JSON.stringify(x);}
function diffBaseline(a,b,limit=100){const all={};for(const k of ['modules','claims','relations','sources','appearance','bridges','documents','axes']){
  const old=a[k]||{},now=b[k]||{},ids=[...new Set([...Object.keys(old),...Object.keys(now)])].sort();const changes=[];
  for (const id of ids){let x=old[id],y=now[id];if(!x)changes.push({id,change:'ADDED',after:y});else if(!y)changes.push({id,change:'REMOVED',before:x});else if(stableJSON(x)!==stableJSON(y))changes.push({id,change:'MODIFIED',before:x,after:y});}
  all[k]={count:changes.length,changes:changes.slice(0,limit),truncated:changes.length>limit};
}return all;}
export function createResearchApi(bundle, context={revision:'LOCAL-VERIFIED-BUNDLE',manifest_sha256:null,origin:'local'}){
  if(bundle?.schema!=='pgk.mcp.publication.v0.8.0')fail('Bundle schema not recognized','INTEGRITY_ERROR');
  const meta=json(bundle,'META-PGK-01.json'), sectionIndex=json(bundle,'achsen/PGK_MODULABSCHNITTE_INDEX.json'),
    sourceRegistry=json(bundle,'quellen/QUELLENREGISTER_A6.json'), axis=json(bundle,'achsen/PGK_ACHSLANDKARTE.json'),
    ew=json(bundle,'erscheinungswelt/META-EW-01.json'), bridges=json(bundle,'bruecken/META-PGK-EW-01.json');
  const modMap=new Map(meta.modules.map(x=>[x.id,x])),claimsMap=new Map(meta.claims.map(x=>[x.id,x])),
    relations=meta.relations.map(edge),relationById=new Map(relations.map(x=>[x.id,x])),
    sourcesMap=new Map(sourceRegistry.sources.map(x=>[x.id,x])),
    sectionMap=new Map(sectionIndex.modules.map(x=>[x.module,x])),
    ewMap=new Map(ew.records.map(x=>[x.id,x])),bridgeMap=new Map(bridges.records.map(x=>[x.id,x]));
  const documentPaths=listPaths(bundle,'forschung/').filter(p=>p.endsWith('.md'));
  const prov=path=>({revision:context.revision,edition:bundle.edition,path,sha256:bundle.files[path]?.sha256||null,source:'approved-publication-bundle',integrity_checked:context.integrity_checked===true});
  function indexRecords(){const records=[];
    for(const m of meta.modules){const p=m.datei,raw=file(bundle,p).content; records.push({id:m.id,kind:'module',title:m.title,status:m.status,path:p,body:`${m.title} ${m.scope} ${raw}`,summary:m.scope});}
    for(const c of meta.claims){records.push({id:c.id,kind:'claim',title:c.aussage,status:c.historischer_status,path:`nachweise/${c.module_id}.json`,body:`${c.aussage} ${c.historischer_status||''} ${c.geltungsbereich||''} ${c.grenze||''} ${c.aussagetyp||''}`,summary:c.aussage});}
    for(const s of sourceRegistry.sources){records.push({id:s.id,kind:'source',title:s.titel,status:s.mcp_source_status,path:'quellen/QUELLENREGISTER_A6.json',body:`${s.titel} ${s.prueftiefe||''} ${s.quelle_typ||''}`,summary:s.mcp_fulltext_available?'Volltext':'Nur Metadaten'});}
    for(const p of documentPaths){let t=file(bundle,p).content;records.push({id:p,kind:'document',title:t.split('\n').find(s=>s.startsWith('#'))?.replace(/^#+\s*/,'')||p,status:'PUBLISHED_RESEARCH_DOCUMENT',path:p,body:t,summary:t.slice(0,250)});}
    for(const r of ew.records){records.push({id:r.id,kind:'appearance',title:r.title||r.titel||r.id,status:r.status||null,path:'erscheinungswelt/META-EW-01.json',body:JSON.stringify(r),summary:r.summary||r.befund||''});}
    for(const r of bridges.records){records.push({id:r.id,kind:'bridge',title:r.title||r.titel||r.id,status:r.status||null,path:'bruecken/META-PGK-EW-01.json',body:JSON.stringify(r),summary:r.summary||r.begruendung||''});}
    return records;}
  const searchRecords=indexRecords();
  function search(a){const query=text(a.query??'').trim();if(query.length>200)fail('query too long');const allowed=['module','claim','source','document','appearance','bridge'];let kinds=a.kinds||allowed;
    if(!Array.isArray(kinds)||kinds.some(x=>!allowed.includes(x)))fail('Unknown search kinds');
    let scored=searchRecords.filter(x=>kinds.includes(x.kind)).map(x=>({record:x,relevance:searchScore(x,query)})).filter(x=>query?x.relevance>0:true);
    if(a.status)scored=scored.filter(x=>norm(x.record.status).includes(norm(a.status)));
    scored.sort((a,b)=>b.relevance-a.relevance||a.record.id.localeCompare(b.record.id));
    const entries=scored.map(({record,relevance})=>({id:record.id,kind:record.kind,title:record.title,status:record.status,path:record.path,excerpt:text(record.summary).slice(0,450),relevance}));
    return {query,kinds,...page(entries,a),warning:'Suche ist lexikalisch. Treffer sind weder fachliche Beziehungen noch wissenschaftliche Bestätigungen.',revision:context.revision};}
  function getModule(a){const m=modMap.get(a.module_id);if(!m)fail('Unknown module','NOT_FOUND');const f=file(bundle,m.datei);
    const output={metadata:m,text:f.content,byte_length:f.bytes,provenance:prov(m.datei)};
    if(a.include_evidence){let p=m.nachweis.path;output.evidence=json(bundle,p);output.evidence_provenance=prov(p);}return output;}
  function getSection(a){const s=sectionMap.get(a.module_id);if(!s)fail('Unknown module','NOT_FOUND');const i=a.section_index;
    if(!Number.isInteger(i)||i<1||i>s.sections.length)fail(`section_index must be 1..${s.sections.length}`);
    const e=s.sections[i-1],f=file(bundle,s.path),buf=new TextEncoder().encode(f.content),piece=buf.slice(e.byte_start,e.byte_end_exclusive);
    return {module_id:a.module_id,section_index:i,section:e,text:new TextDecoder('utf8',{fatal:true}).decode(piece),byte_length:piece.length,provenance:prov(s.path)};}
  function getClaim(a){const c=claimsMap.get(a.claim_id);if(!c)fail('Unknown claim','NOT_FOUND');const p=`nachweise/${c.module_id}.json`;
    const availableSourceDiagnostics=(c.quellen||[]).filter(q=>available(sourcesMap.get(q.source_id)||{})).map(q=>{
      const source=sourcesMap.get(q.source_id),lines=file(bundle,source.datei).content.split(/\r?\n/);
      const sought=text(q.anchor||'').split(':')[0].trim(),matches=sought?lines.flatMap((line,i)=>line.includes(sought)?[i+1]:[]):[];
      const recorded=q.line_start??null;
      return {source_id:q.source_id,recorded_line_start:recorded,anchor:q.anchor,matching_lines:matches.slice(0,12),status:matches.length&&!matches.includes(recorded)?'DOCUMENTED_POINTER_DIFFERENT_FROM_TEXT_ANCHOR':matches.length?'ANCHOR_FOUND_AT_RECORDED_LINE':'EXACT_ANCHOR_NOT_FOUND',warning:'Suchdiagnostik; keine stille Ersetzung des historischen Quellenankers.'};
    });
    return {claim:c,module_id:c.module_id,provenance:prov(p),source_text_availability:c.quellen?.map(q=>({source_id:q.source_id,fulltext_available:available(sourcesMap.get(q.source_id)||{})}))??[],source_anchor_diagnostics:availableSourceDiagnostics};}
  function getRelations(a){const dir=a.direction||'both';if(!DIRECTIONS.has(dir))fail('Invalid direction');const depth=a.depth??1;if(![1,2].includes(depth))fail('depth must be 1 or 2');
    if(Boolean(a.claim_id)===Boolean(a.module_id))fail('Exactly one of claim_id or module_id required');
    if(a.claim_id){if(!claimsMap.has(a.claim_id))fail('Unknown claim','NOT_FOUND');let frontier=new Set([a.claim_id]),visited=new Set(frontier),out=[];
      for(let d=1;d<=depth;d++){const next=new Set();for(let r of relations){let detected=[];
        if(frontier.has(r.from)&&dir!=='incoming')detected.push('outgoing');
        if(frontier.has(r.to)&&dir!=='outgoing')detected.push('incoming');
        for(let matched of detected){if(!out.some(x=>x.relation_id===r.id&&x.traversal===matched)){let record={relation_id:r.id,recorded_direction:{from:r.from,to:r.to},traversal:matched,step:d,type:r.type,record:r.record};if(a.include_evidence===false)record={...record,record:{eintrag:{...r.record.eintrag,belege:[]},qualifizierung_v06:r.record.qualifizierung_v06}};out.push(record);}
          next.add(matched==='outgoing'?r.to:r.from);}
      } frontier=new Set([...next].filter(x=>!visited.has(x)));for(let id of frontier)visited.add(id);if(!frontier.size)break;}
      out.sort((a,b)=>a.step-b.step||a.relation_id.localeCompare(b.relation_id));return {claim_id:a.claim_id,direction:dir,depth,...page(out,a),warning:DOC_MARK,revision:context.revision};}
    if(!modMap.has(a.module_id))fail('Unknown module','NOT_FOUND');
    let links=[];for(const m of meta.modules){for(const [kind,items] of Object.entries(m.kuriert||{}))for(const x of items){if((m.id===a.module_id&&dir!=='incoming')||(x.ziel===a.module_id&&dir!=='outgoing')){
      const rid=x.beleg_relation_id,rel=relationById.get(rid);links.push({from_module:m.id,to_module:x.ziel,recorded_direction:'SOURCE_TO_TARGET',traversal:m.id===a.module_id?'outgoing':'incoming',kind,curated:x,underlying_claim_relation:rel?.record||null});}
    }if(a.include_candidates!==false){for(const x of m.offene_kandidaten||[])if((m.id===a.module_id&&dir!=='incoming')||(x.ziel===a.module_id&&dir!=='outgoing'))links.push({from_module:m.id,to_module:x.ziel,kind:'OPEN_CANDIDATE',candidate:x});}
    if(a.include_text_refs===true){for(const x of m.textbezuege||[])if((m.id===a.module_id&&dir!=='incoming')||(x.ziel===a.module_id&&dir!=='outgoing'))links.push({from_module:m.id,to_module:x.ziel,kind:'TEXT_OR_SEARCH_ONLY',text_reference:x});}}
    links.sort((x,y)=>x.from_module.localeCompare(y.from_module)||x.to_module.localeCompare(y.to_module));
    return {module_id:a.module_id,direction:dir,...page(links,a),warning:'Modulanschlüsse sind qualifizierte Navigation, keine zusätzliche Beweisstufe. Suchbezüge und offene Kandidaten bleiben getrennt.',revision:context.revision};
  }
  function getSource(a){const src=sourcesMap.get(a.source_id);if(!src)fail('Unknown source','NOT_FOUND');
    if(!available(src)){return {source:src,fulltext_available:false,reason:'Original source not released in public PGK bundle; metadata only. No invented quotation.',provenance:prov('quellen/QUELLENREGISTER_A6.json')};}
    const f=file(bundle,src.datei);let lines=f.content.split(/\r?\n/),start=a.line_start??1,end=a.line_end??Math.min(lines.length,start+199);
    if(!Number.isInteger(start)||start<1||!Number.isInteger(end)||end<start||end>lines.length)fail('Invalid line range');
    if(end-start>300)fail('Use a line window of up to 301 lines');
    const anchor=text(a.anchor||'').trim();if(anchor.length>150)fail('anchor query too long');
    const anchor_matches=anchor?lines.flatMap((line,i)=>line.includes(anchor)?[i+1]:[]).slice(0,30):[];
    return {source:src,fulltext_available:true,fulltext_lines:lines.length,requested_lines:{start,end},has_more:end<lines.length,anchor_query:anchor||null,anchor_matches,excerpt:lines.slice(start-1,end).map((s,i)=>({line:start+i,text:s})),
      citation_warning:'Historische Quellenanker und präzisierte Fundstellen müssen getrennt dokumentiert werden; hier wird die angeforderte Originalzeile geliefert.',provenance:prov(src.datei)};}
  function getDocument(a){if(!documentPaths.includes(a.path))fail('Document not registered for public MCP access','NOT_FOUND');
    const f=file(bundle,a.path),lines=f.content.split('\n');const start=a.line_start??1;
    if(!Number.isInteger(start)||start<1||start>lines.length)fail('Invalid line_start');const limit=limitOf(a.max_lines,100,500);let end=Math.min(lines.length,start+limit-1);
    return {path:a.path,total_lines:lines.length,returned_lines:{start,end},has_more:end<lines.length,text:lines.slice(start-1,end).join('\n'),provenance:prov(a.path)};}
  function findRelated(a){const query=text(a.query).trim();if(query.length<3||query.length>300)fail('query must have 3..300 characters');
    const kinds=['module','claim','document','appearance','bridge'];const found=searchRecords.filter(x=>kinds.includes(x.kind)).map(x=>({id:x.id,kind:x.kind,title:x.title,path:x.path,status:x.status,score:searchScore(x,query)})).filter(x=>x.score>0).sort((x,y)=>y.score-x.score||x.id.localeCompare(y.id));
    let axs=[...(axis.erkenntnisbereiche||[]).map(x=>({...x,kind:'erkenntnisbereich'})),...(axis.spiegelachsen||[]).map(x=>({...x,kind:'spiegelachse'}))].map(x=>({...x,score:score(JSON.stringify(x),query)})).filter(x=>x.score>0).sort((x,y)=>y.score-x.score);
    return {query,candidates:page(found,a),axes:axs.slice(0,10),warning:'Lexikalisch ermittelte FIND-Kandidaten; keine neue fachliche Beziehung, kein Eintrag oder Freigabe. Negative und widersprechende Claims mitprüfen.',revision:context.revision};}
  function getAxes(a){const kind=a.kind||'all';if(!['all','area','mirror'].includes(kind))fail('invalid kind');let res=[];
    if(kind!=='mirror')res.push(...(axis.erkenntnisbereiche||[]).map(x=>({...x,kind:'area'})));
    if(kind!=='area')res.push(...(axis.spiegelachsen||[]).map(x=>({...x,kind:'mirror'})));
    if(a.id)res=res.filter(x=>x.id===a.id);
    if(a.query)res=res.filter(x=>score(JSON.stringify(x),a.query)>0);
    let assignments={};for(let v of res)assignments[v.id]=meta.modules.filter(m=>m.erkenntnisachsen?.includes(v.id)||m.spiegelachsen?.some(x=>x.achse===v.id)).map(x=>x.id);
    return {areas_total:(axis.erkenntnisbereiche||[]).length,mirrors_total:(axis.spiegelachsen||[]).length,axes:res,assignments,warning:'Spiegelachsen sind zunächst quellennahe Kontraste, keine automatischen Modulspiegel.',provenance:prov('achsen/PGK_ACHSLANDKARTE.json')};}
  function getAppearance(a){if(!a.id)return {schema:ew.schema,edition:ew.edition,status:ew.scientific_status,records:page(ew.records,a),open_intake:ew.open_intake||[],provenance:prov('erscheinungswelt/META-EW-01.json')};
    const r=ewMap.get(a.id);if(!r)fail('Unknown appearance record','NOT_FOUND');return {record:r,provenance:prov('erscheinungswelt/META-EW-01.json')};}
  function getBridge(a){if(!a.id)return {schema:bridges.schema,edition:bridges.edition,status:bridges.scientific_status,records:page(bridges.records,a),open_candidates:bridges.open_candidates||[],relationship_types:bridges.relationship_types||[],provenance:prov('bruecken/META-PGK-EW-01.json')};
    const r=bridgeMap.get(a.id);if(!r)fail('Unknown bridge record','NOT_FOUND');return {record:r,provenance:prov('bruecken/META-PGK-EW-01.json')};}
  function validateDraft(a){const type=a.type||'batch',draft=a.draft;if(!obj(draft))fail('draft must be an object');if(JSON.stringify(draft).length>30000)fail('Draft too large (>30k)');
    const errors=[],warnings=[],knownClaims=new Set(claimsMap.keys()),knownSources=new Set(sourcesMap.keys()),knownModules=new Set(modMap.keys()),knownAppearances=new Set(ewMap.keys());
    const lists=type==='batch'?draft:{[type]:Array.isArray(draft)?draft:[draft]};
    const asList=x=>x==null?[]:Array.isArray(x)?x:[x];
    const add=(message)=>errors.push(message);const notice=m=>warnings.push(m);
    const modules=asList(lists.modules||lists.module),claims=asList(lists.claims||lists.claim),relations=asList(lists.relations||lists.relation),sources=asList(lists.sources||lists.source),appearances=asList(lists.appearance||lists.appearances),bridgeDrafts=asList(lists.bridges||lists.bridge);
    let ids=new Set();function unique(o,known,context){if(!obj(o)||!text(o.id).trim()){add(`${context}: missing id`);return;}if(known.has(o.id))add(`${context}: id already exists: ${o.id}`);if(ids.has(o.id))add(`duplicate draft id: ${o.id}`);ids.add(o.id);}
    for(const x of modules){unique(x,knownModules,'module');if(!x.title||!x.scope)add('module: title and scope required');}
    for(const x of sources){unique(x,knownSources,'source');if(!x.titel)add('source: titel required');}
    const claimFuture=new Set([...knownClaims,...claims.map(x=>x.id)]),sourceFuture=new Set([...knownSources,...sources.map(x=>x.id)]),moduleFuture=new Set([...knownModules,...modules.map(x=>x.id)]);
    for(const x of claims){unique(x,knownClaims,'claim');if(!moduleFuture.has(x.module_id))add(`claim ${x.id}: unknown module ${x.module_id}`);if(!x.aussage||!x.geltungsbereich||!x.grenze)add(`claim ${x.id}: aussage, geltungsbereich and grenze required`);
       for(const z of x.quellen||[])if(!sourceFuture.has(z.source_id))add(`claim ${x.id}: unknown source ${z.source_id}`);}
    for(const r of relations){const x=r.eintrag||r;unique(x,new Set(relationById.keys()),'relation');const from=x.von??x.from_claim,to=x.nach??x.to_claim;if(!claimFuture.has(from)||!claimFuture.has(to))add(`relation ${x.id}: unknown claim endpoint ${from}→${to}`);if(!x.relation&&!x.relation_type)add(`relation ${x.id}: missing relation type`);for(const z of x.belege||[])if(!sourceFuture.has(z.source_id))add(`relation ${x.id}: unknown source ${z.source_id}`);}
    for(const x of appearances){unique(x,knownAppearances,'appearance');if(!x.title&&!x.titel)add(`appearance ${x.id}: missing title`);if(!x.sources?.length&&!x.quellen?.length)add(`appearance ${x.id}: observation needs original source references`);}
    const appFuture=new Set([...knownAppearances,...appearances.map(x=>x.id)]);
    for(const x of bridgeDrafts){unique(x,new Set(bridgeMap.keys()),'bridge');let kind=x.relationship_type||x.beziehungstyp;if(!bridges.relationship_types.includes(kind))add(`bridge ${x.id}: invalid relationship_type`);
      for(const id of x.pgk_claim_ids||[])if(!claimFuture.has(id))add(`bridge ${x.id}: unknown PGK claim ${id}`);
      for(const id of x.appearance_ids||[])if(!appFuture.has(id))add(`bridge ${x.id}: unknown appearance ${id}`);
      if(!(x.pgk_claim_ids||[]).length||!(x.appearance_ids||[]).length)add(`bridge ${x.id}: both domains need IDs`);
      if(!x.geltungsgrenze&&!x.grenze)notice(`bridge ${x.id}: explicit limits should be documented`);}
    if(!Object.keys(lists).some(x=>['module','modules','claim','claims','relation','relations','source','sources','appearance','appearances','bridge','bridges'].includes(x)))add('No recognized draft objects');
    return {valid:errors.length===0,technical_valid:errors.length===0,review_scope:'STRUCTURE_AND_REFERENCES_ONLY',tsm_relevance_review:'NOT_PERFORMED_BY_MCP',estimate_classification:'NOT_PERFORMED_BY_MCP',publication_ready:false,human_approval_required:true,errors,warnings,counts:{modules:modules.length,claims:claims.length,relations:relations.length,sources:sources.length,appearances:appearances.length,bridges:bridgeDrafts.length},scientific_approval:false,writes_performed:false,warning:'Syntactic and referential draft preflight only. Technical validity does not classify estimates, judge research relevance or authorize publication.',revision:context.revision};}
  const actions={
    pgk_status:()=>({revision:context.revision,edition:bundle.edition,integrity_checked:context.integrity_checked===true,integrity_level:context.integrity_level||null,origin:context.origin,manifest_sha256:context.manifest_sha256||null,bundle_sha256:context.bundle_sha256||null,counts:bundle.counts,
      original_sources_fulltext:sourceRegistry.sources.filter(available).length,original_sources_metadata_only:sourceRegistry.sources.filter(x=>!available(x)).length,
      epistemic_boundary:'Korpus und PGK formal getrennt; keine automatische Evidenztransitivität',
      version_note:'Default reads currently verified bundle; optional revision pins a GitHub commit across research calls.'}),
    pgk_search:search, pgk_get_module:getModule,pgk_get_section:getSection,pgk_get_claim:getClaim,pgk_get_relations:getRelations,
    pgk_get_source:getSource,pgk_get_document:getDocument,pgk_find_related:findRelated,pgk_get_axes:getAxes,
    pgk_get_appearance:getAppearance,pgk_get_bridge:getBridge,pgk_validate_draft:validateDraft
  };
  return {
    call(name,args={}){if(!actions[name])fail(`Unknown MCP tool: ${name}`,'NOT_FOUND');return actions[name](args||{});},
    compareTo(other,{limit=100}={}){return {from_version:other.base_research_version||'unspecified',to_version:bundle.base_research_version,changes:diffBaseline(makeBaseline(other),makeBaseline(bundle),limit),revision:context.revision,warning:'Different revisions are compared as recorded, no scientific promotion or silent rewrite.'};},
    model:meta,sourceRegistry,axes:axis,bundle,context
  };
}
const s={type:'object',additionalProperties:false,properties:{}};
const str=(description)=>({type:'string',description});
const integer=(description)=>({type:'integer',description});
const shared={revision:{type:'string',description:'Optional GitHub commit SHA (40 hex); fixes research snapshot across calls.'}};
function tool(name,description,properties={},required=[]){return {name,description,annotations:{readOnlyHint:true,destructiveHint:false,idempotentHint:true,openWorldHint:true},inputSchema:{type:'object',additionalProperties:false,properties:{...properties,...shared},required}};}
const paging={limit:integer('Max 50 (or tool-specific bound).'),offset:integer('Zero-based pagination offset.')};
export const TOOLS=[
  tool('pgk_status','Current verified research inventory, provenance, data/source availability, revision.'),
  tool('pgk_search','Search recorded modules, claims, research reports, negatives, sources, appearance/bridges; no inference.',{query:str('Query or empty to list.'),kinds:{type:'array',items:{type:'string',enum:['module','claim','document','source','appearance','bridge']}},status:str('Optional literal status filter.'),...paging}),
  tool('pgk_get_module','Full authoritative PGK module text, metadata and optional paired evidence.',{module_id:str('PGKM-NNN'),include_evidence:{type:'boolean'}},['module_id']),
  tool('pgk_get_section','Byte-faithful one indexed module section by 1-based section number.',{module_id:str('PGKM-NNN'),section_index:integer('1-based section index.')},['module_id','section_index']),
  tool('pgk_get_claim','Original claim with scope, limits, statuses, citations, source availability.',{claim_id:str('PGKC-NNN or A6N-CNNN')},['claim_id']),
  tool('pgk_get_relations','Directed claim edges and curated module links; reverse browsing NEVER reverses scientific implication.',{claim_id:str('Claim starting point'),module_id:str('Module starting point'),direction:{type:'string',enum:['both','incoming','outgoing']},depth:{type:'integer',enum:[1,2]},include_evidence:{type:'boolean'},include_candidates:{type:'boolean'},include_text_refs:{type:'boolean'},...paging}),
  tool('pgk_get_source','Source metadata and ONLY released original text and precise line windows.',{source_id:str('SRC-NNN'),line_start:integer('1-based original line.'),line_end:integer('Last 1-based line, inclusive.'),anchor:str('Optional exact phrase to locate in available original text; does not alter cited line.')},['source_id']),
  tool('pgk_get_document','Released scientific paper/protocol/reproduction document by exact allowlisted path.',{path:str('Published forschung/... md path'),line_start:integer('1-based'),max_lines:integer('Max 500')},['path']),
  tool('pgk_find_related','Non-authoritative lexical suggestions of claims, axes, modules and negative findings; no updates.',{query:str('Research question'),...paging},['query']),
  tool('pgk_compare_versions','Typed diff of an older GitHub-commit publication against the selected current revision (or v0.7.4 baseline).',{baseline_revision:str('Optional earlier 40-hex GitHub SHA. Omit for bundled v0.7.4 baseline.'),limit:integer('Max changes returned per category; default 100, max 200')}),
  tool('pgk_validate_draft','Stateless schema/reference preflight of curated human/TSM drafts. Never writes or approves.',{type:{type:'string',enum:['batch','module','claim','relation','source','appearance','bridge']},draft:{type:'object',description:'Proposed object or grouped module/claims/relations/sources/appearance/bridges arrays. Maximum 30 kB.'}},['draft']),
  tool('pgk_get_axes','Explicit areas and mirror/contrast axes including their module assignments.',{kind:{type:'string',enum:['all','area','mirror']},id:str('Optional exact axis ID'),query:str('Optional lexical filter')}),
  tool('pgk_get_appearance','Observed world registry and individual empirical records, including empty-state metadata.',{id:str('Registered empirical record ID'),...paging}),
  tool('pgk_get_bridge','Qualified PGK ↔ observed world bridges and open candidates, including empty-state metadata.',{id:str('Bridge ID'),...paging}),
];
export {makeBaseline,diffBaseline,fail};
