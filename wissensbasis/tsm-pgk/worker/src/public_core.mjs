/* TSM–PGK public-essence read model.
 * Original research modules remain internal. This exposes derived approved
 * source content only, with explicit preview/review status.
 */
import {TOOLS as BASE_TOOLS} from './core.mjs';
import {COMPARISON_TOOLS,makeComparisonApi} from './comparison_api.mjs';

export const TOOLS=BASE_TOOLS.map(t=>{
  const v={...t, inputSchema:{...t.inputSchema, properties:{...t.inputSchema.properties}}};
  if(t.name==='pgk_get_module')v.description='Public derived module view, NOT the original private module. Review findings are separately marked.';
  if(t.name==='pgk_get_section')v.description='One section of a public derived module view. NOT a byte-faithful private original section.';
  if(t.name==='pgk_get_source')v.description='Public source metadata and only genuinely released public original text. Missing sources return no fulltext.';
  if(t.name==='pgk_get_document'){
    v.description='A public-allowlisted research document or released formal paper, with explicit source type.';
    v.inputSchema.properties.path={type:'string',description:'Public README.md, ARBEITSSTAND.md, FORSCHUNGSKARTE.md, erkenntnisse/PGKM-NNN.md, forschung/..., erscheinungswelt/*.md, beweise/A6N-T1_SRC-078.md'};
  }
  if(t.name==='pgk_compare_versions')v.description='Diff two compatible public GitHub publications. Requires a real earlier 40-hex commit; no fabricated v0.7.4 baseline.';
  if(t.name==='pgk_get_relations')v.description='Directed curated claim edges; editorial review-only topic links are separate and cannot reverse causal or inferential direction.';
  if(t.name==='pgk_search'){
    v.description='Search the public open PGK research memory, including formal, negative and hypothetical findings. TSM judges relevance and estimates.';
    v.inputSchema.properties.kinds={type:'array',items:{type:'string',enum:['module','claim','source','document','appearance','bridge','finding','passport','relation','analogy','anchor','model_gap','research_extension']}};
  }
  return v;
}).concat([{name:'pgk_get_topic_relations',description:'Navigate noncanonical topic-level research links as exploratory hypotheses, NOT directed Claim-to-Claim graph edges.',inputSchema:{type:'object',properties:{topic:{type:'string',description:'Topic name or fragment, including historical PGK identifiers'},direction:{type:'string',enum:['both','from','to']},revision:{type:'string',description:'Optional exact 40-hex GitHub commit SHA, resolved by the MCP loader'},offset:{type:'integer',minimum:0},limit:{type:'integer',minimum:1,maximum:100}}}},
{name:'pgk_get_research_record',description:'Read a complete public research finding, evidence passport or exploratory topic relation by stable ID. Publication inclusion does not imply scientific validation or canonical authority. Private original fulltexts are not embedded.',inputSchema:{type:'object',properties:{record_id:{type:'string',description:'Exact public research record ID'},record_kind:{type:'string',enum:['finding','passport','relation']},revision:{type:'string',description:'Optional exact 40-hex GitHub commit SHA'}},required:['record_id']}}]).concat(COMPARISON_TOOLS).map(tool=>({
  ...tool,
  annotations:{...tool.annotations,readOnlyHint:true,openWorldHint:true,destructiveHint:false}
}));
const s=x=>String(x??'');
const lower=x=>s(x).normalize('NFKC').replace(/[\u2010-\u2015\u2212\uFE58\uFE63\uFF0D]/g,'-').toLocaleLowerCase('de-DE');
const MAX=100;
function fail(message,kind='INVALID_ARGUMENT'){const e=new Error(message);e.kind=kind;throw e;}
function count(a,k,d=20){const v=a?.[k]??d;const n=Number(v);if(!Number.isInteger(n)||n<(k==='limit'?1:0)||n>(k==='limit'?MAX:100000))fail(`${k} invalid`);return n;}
function page(items,a={}){const offset=count(a,'offset',0),limit=count(a,'limit',20);return {total:items.length,offset,limit,has_more:offset+limit<items.length,items:items.slice(offset,offset+limit)};}
function score(h,q){
  const v=lower(h), needle=lower(q).trim();if(!needle)return 1;
  if(v.includes(needle))return 120+(v===needle?80:0);
  const ts=[...new Set(needle.split(/[\s,;:/]+/).filter(x=>x.length>=3))];
  if(!ts.length)return 0;
  const hits=ts.filter(t=>v.includes(t)).length;
  return hits? Math.round(50*hits/ts.length) +(hits===ts.length?10:0) : 0;
}
const jsonFile=(bundle,p)=>{const rec=bundle.files[p];if(!rec)fail('Public file unavailable: '+p,'NOT_FOUND');return JSON.parse(rec.content);};
const file=(bundle,p)=>{const rec=bundle.files[p];if(!rec)fail('Public file unavailable: '+p,'NOT_FOUND');return rec;};
function index(bundle) {
 const modules=jsonFile(bundle,'daten/module.json').modules;
 const claims=jsonFile(bundle,'daten/claims.json').claims;
 const relations=jsonFile(bundle,'daten/relations.json').relations;
 const sources=jsonFile(bundle,'daten/sources.json').sources;
 const axes=jsonFile(bundle,'daten/axes.json');
 const appearance=jsonFile(bundle,'daten/appearance.json').records;
 const bridges=jsonFile(bundle,'daten/bridges.json').records;
 const findings=jsonFile(bundle,'daten/research_findings.json').findings.filter(x=>x.public_research_memory===true);
 const passports=jsonFile(bundle,'daten/evidence_passports.json').passports.filter(x=>x.public_research_memory===true);
 const reviewLinks=jsonFile(bundle,'daten/review_relations.json').relations.filter(x=>x.public_research_memory===true);
 const state=jsonFile(bundle,'daten/research_state.json');
 return {modules,claims,relations,sources,axes,appearance,bridges,findings,passports,reviewLinks,state,
  mmap:new Map(modules.map(x=>[x.id,x])),cmap:new Map(claims.map(x=>[x.id,x])),smap:new Map(sources.map(x=>[x.id,x]))};
}
function sourceAvailability(src) {return src?.original_public?'ORIGINAL_PUBLIC':'ORIGINAL_PRIVATE_UNAVAILABLE';}
function sectionsFor(t){
 const heads=[...t.matchAll(/^#{1,3}\s+.+$/gm)];
 if(!heads.length)return [{index:1,heading:'Text',text:t}];
 return heads.map((h,i)=>({index:i+1,heading:h[0].trim(),text:t.slice(h.index, i+1<heads.length?heads[i+1].index:t.length).trim()}));
}
function identity(x){return JSON.stringify(x,Object.keys(x??{}).sort());}
export function createPublicResearchApi(bundle, context={revision:'LOCAL_PREVIEW_ONLY'}) {
 if(bundle?.schema!=='pgk.mcp.public-essence.v1')fail('Wrong public essence bundle','INTEGRITY_ERROR');
 const idx=index(bundle);
 idx.comparison=makeComparisonApi(bundle,{revision:context.revision||'LOCAL_PREVIEW_ONLY'});
 const ctx={...context,source_kind:'PUBLIC_DERIVED_VIEW',public_preview:bundle.publication_approved!==true};
 const sourceStatus=Object.fromEntries(idx.sources.map(x=>[x.id,sourceAvailability(x)]));
 function status(){
   return {schema:bundle.schema,revision:ctx.revision,provenance:ctx,
    inventory:{modules:idx.modules.length,claims:idx.claims.length,relations:idx.relations.length,sources:idx.sources.length,
      research_findings_public:idx.findings.length,evidence_passports_public:idx.passports.length,
      topic_research_links_public:idx.reviewLinks.length,appearance:idx.appearance.length,bridges:idx.bridges.length,
      appearance_analogy_candidates:idx.comparison.cmp.length,appearance_external_anchors:idx.comparison.anchors.length,
      model_gaps:idx.comparison.gaps.length,additional_research_extensions:idx.comparison.extras.length},
    canonical_baseline:idx.state.canonical_baseline,
    research_guards:idx.state.fixed_contracts,
    publication_status:bundle.publication_approved?'PUBLIC_RESEARCH_RELEASE':'PUBLIC_RESEARCH_PREVIEW_NOT_APPROVED_FOR_GITHUB_COMMIT',
    source_note:'Open PGK research memory: inclusion is not a claim of scientific verification. Only genuinely released public original source text is returned.'};
 }
 function search(a={}){
   let q=s(a.query).trim();
   if(q.length>250)fail('Search query too long');
   const kinds=a.kinds?.length?new Set(a.kinds):null;
   const candidates=[];
   const add=(kind,rec,title,body,kindSource='PUBLIC_DERIVED_VIEW',more={})=>{
     if(kinds&&!kinds.has(kind))return;
     const sc=score(title,q)*2+score(body,q);
     if(sc)candidates.push({kind,id:rec.id||rec.path||title,title,preview:s(body).slice(0,500),score:sc,
       source_kind:kindSource,...more});
   };
   idx.modules.forEach(x=>add('module',x,`${x.id} ${x.titel}`,x.geltungsbereich+' '+(x.claim_ids||[]).join(' ')));
   idx.claims.forEach(x=>add('claim',x,`${x.id} ${x.module_id}`,`${x.aussage} ${x.geltungsbereich} ${x.historischer_status}`,
    'PUBLIC_DERIVED_CLAIM',{historical_status:x.historischer_status}));
   idx.sources.forEach(x=>add('source',x,x.id,`${x.source_kind} ${x.availability}`,sourceAvailability(x),{available_fulltext:!!x.original_public}));
   idx.findings.forEach(x=>add('finding',x,`${x.originalkennung} ${x.id}`,
     `${x.kernaussage} ${x.ergebnisstatus} ${x.modellzweig} ${x.guards} ${x.pgkm_vorschlag.join(' ')}`,
     'PUBLIC_OPEN_RESEARCH_FINDING',{scientific_confirmation_not_implied:true}));
   idx.passports.forEach(x=>add('passport',x,`${x.forschungskennung} ${x.id}`,
      `${JSON.stringify(x.ergebnis)} ${x.testvertrag} ${x.gegenbefunde_und_geltungsgrenzen}`,
      'PUBLIC_OPEN_EVIDENCE_PASSPORT',{scientific_confirmation_not_implied:true}));
   idx.reviewLinks.forEach(x=>add('relation',x,`${x.id} ${x.from_topic} ${x.to_topic}`,`${x.relation_type} ${x.scope} ${x.research_extension}`,'PUBLIC_TOPIC_LEVEL_RESEARCH_LINK',{canonical_edge:false}));
   idx.comparison.cmp.forEach(x=>add('analogy',x,`${x.id} ${x.titel_oder_kennung}`,`${x.kerninhalt} ${x.status_im_pgk} ${x.anker_ids.join(' ')} ${x.modell_luecke}`,'EXPLORATORY_NOT_TESTED',{scientific_confirmation_not_implied:true}));
   idx.comparison.anchors.forEach(x=>add('anchor',x,`${x.id} ${x.titel}`,`${x.fachgebiet} ${x.externer_anker} ${x.beobachtungsparameter}`,'EXTERNAL_COMPARISON_ANCHOR',{scientific_confirmation_not_implied:true}));
   idx.comparison.gaps.forEach(x=>add('model_gap',x,`${x.id} ${x.forschungsfrage}`,`${x.festgestellte_luecke} ${x.naechster_modellschritt} ${x.pgk_bezuege}`,'MODEL_TRANSLATION_GAP',{research_open:true}));
   idx.comparison.extras.forEach(x=>add('research_extension',x,`${x.id} ${x.titel}`,`${x.statement} ${x.limit}`,'OPEN_RESEARCH_EXTENSION',{scientific_confirmation_not_implied:true}));
   for(const p of Object.keys(bundle.files)){
     if(p.endsWith('.md') && !p.startsWith('erkenntnisse/'))add('document',{id:p},p,bundle.files[p].content.slice(0,1000),
       p.startsWith('beweise/')?'ORIGINAL_PUBLIC':'PUBLIC_DERIVED_VIEW');
   }
   const filtered=a.status?candidates.filter(x=>(x.historical_status||x.source_kind)===a.status):candidates;
   filtered.sort((x,y)=>y.score-x.score||x.id.localeCompare(y.id,'de'));
   return {...page(filtered,a),query:q,revision:ctx.revision,
      caveat:'Lexical navigational results; relevance, model forks and scientific judgments belong to TSM.'};
 }
 function getModule(a={}){
   const m=idx.mmap.get(a.module_id);if(!m)fail('Module not found','NOT_FOUND');
   const p=`erkenntnisse/${m.id}.md`,text=file(bundle,p).content;
   const found=idx.findings.filter(f=>f.pgkm_vorschlag.includes(m.id)||f.pgkm_bestand.includes(m.id));
   return {module:m,public_text:text,source_kind:'PUBLIC_DERIVED_VIEW',is_full_original:false,
    original_available:false,linked_review_findings:found.map(x=>({id:x.id,originalkennung:x.originalkennung,
      status:x.ergebnisstatus,public_research_memory:true})).slice(0,60),
    linked_findings_count:found.length,revision:ctx.revision,
    caveat:'This document is a curated secondary public view. Private original module and evidence text are not returned.'};
 }
 function getSection(a={}){
   const m=idx.mmap.get(a.module_id);if(!m)fail('Module not found','NOT_FOUND');
   const ss=sectionsFor(file(bundle,`erkenntnisse/${m.id}.md`).content);
   const i=Number(a.section_index);if(!Number.isInteger(i)||i<1||i>ss.length)fail('Section index not found','NOT_FOUND');
   return {module_id:m.id,...ss[i-1],section_count:ss.length,source_kind:'PUBLIC_DERIVED_SECTION',
     is_full_original:false,revision:ctx.revision};
 }
 function getClaim(a={}){
   const c=idx.cmap.get(a.claim_id);if(!c)fail('Claim not found','NOT_FOUND');
   return {claim:c,source_kind:'PUBLIC_DERIVED_CLAIM',sources:c.source_ids.map(id=>({source_id:id,access:sourceStatus[id]||'UNKNOWN'})),
     revision:ctx.revision,caveat:'Claim text is a curated public registry entry, not its original research artifact.'};
 }
 function getRelations(a={}){
   if(!a.claim_id&&!a.module_id)fail('claim_id or module_id is required');
   if(a.claim_id&&!idx.cmap.has(a.claim_id))fail('Unknown claim','NOT_FOUND');
   if(a.module_id&&!idx.mmap.has(a.module_id))fail('Unknown module','NOT_FOUND');
   const direction=a.direction||'both';if(!['incoming','outgoing','both'].includes(direction))fail('Invalid direction');
   const depth=a.depth??1;if(![1,2].includes(depth))fail('Depth must be 1 or 2');
   const start=a.claim_id?[a.claim_id]:idx.claims.filter(c=>c.module_id===a.module_id).map(c=>c.id);
   const reached=new Set(start),edges=new Map();let front=start;
   for(let d=0;d<depth;d++){
     const next=[];
     for(const edge of idx.relations){
       const forward=direction!=='incoming'&&front.includes(edge.from);
       const reverse=direction!=='outgoing'&&front.includes(edge.to);
       if(forward||reverse){
         edges.set(edge.id,edge);
         for(const id of [edge.from,edge.to])if(!reached.has(id)){reached.add(id);next.push(id);}
       }
     }
     front=next;
   }
   const ret={edges:page([...edges.values()],a),claim_ids:[...reached],source_kind:'CURATED_DIRECTED_GRAPH',
     warning:'Reverse navigation does not reverse the scientific direction of an edge.',revision:ctx.revision};
   if(a.include_candidates){
     const owned=new Set(a.claim_id?[a.claim_id]:start);
     ret.separate_review_links=idx.reviewLinks.filter(x=>
        x.link_level==='TYPED_CLAIM_LINK' &&
        [...(x.from_claim_ids||[]),...(x.to_claim_ids||[])].some(id=>owned.has(id))
       ).slice(0,20).map(x=>({...x,canonical_edge:false,
         direction_preserved:true,typed_claim_endpoints:true}));
     ret.note='Topic-level research relations are accessible separately via pgk_get_topic_relations; no claim endpoints are inferred from topic names.';
   }
   return ret;
 }
 function getTopicRelations(a={}){
   const topic=lower(a.topic).trim(),direction=a.direction||'both';
   if(!['both','from','to'].includes(direction))fail('Invalid topic relation direction');
   const matches=idx.reviewLinks.filter(x=>{
     if(!topic)return true;
     return (direction!=='to'&&lower(x.from_topic).includes(topic))||
       (direction!=='from'&&lower(x.to_topic).includes(topic));
   });
   return {relations:page(matches,a),relation_level:'TOPIC_TO_TOPIC_EXPLORATION',
     canonical_claim_edges:false,scientific_confirmation_not_implied:true,
     revision:ctx.revision,note:'Topic relations are research suggestions, not mechanically authorized PGKC-to-PGKC connections.'};
 }
 function getResearchRecord(a={}){
   const id=s(a.record_id).trim(),kind=a.record_kind||null;
   if(!id || id.length>200)fail('record_id required');
   if(kind&&!['finding','passport','relation'].includes(kind))fail('Invalid record_kind');
   const tables=[['finding',idx.findings],['passport',idx.passports],['relation',idx.reviewLinks]];
   const matches=tables.filter(([k])=>!kind||kind===k).flatMap(([k,rows])=>
      rows.filter(r=>r.id===id&&r.public_research_memory===true).map(record=>({kind:k,record})));
   if(matches.length!==1)fail('Public research record unavailable','NOT_FOUND');
   const match=matches[0];
   return {record_id:id,record_kind:match.kind,record:match.record,
      source_kind:'PUBLIC_OPEN_DERIVED_RESEARCH_RECORD',scientific_confirmation_not_implied:true,
      is_original_fulltext:false,available_fulltext:false,revision:ctx.revision,
      note:'Complete public research-memory record, not a scientific endorsement. Private originals not contained in this response.'};
 }
 function getSource(a={}){
   const src=idx.smap.get(a.source_id);if(!src)fail('Source unknown','NOT_FOUND');
   const access=sourceAvailability(src);
   if(!src.original_public)return {source:src,source_kind:access,available_fulltext:false,content:null,revision:ctx.revision};
   if(src.id!=='SRC-078')fail('Released source has no allowlisted text file','INTEGRITY_ERROR');
   const full=file(bundle,'beweise/A6N-T1_SRC-078.md').content,lines=full.split(/\r?\n/);
   const n1=a.line_start==null?1:Number(a.line_start);
   const n2=a.line_end==null?Math.min(lines.length,n1+199):Number(a.line_end);
   if(!Number.isInteger(n1)||!Number.isInteger(n2)||n1<1||n2<n1||n2-n1>499)fail('Invalid line range');
   const anchor=a.anchor?lines.findIndex(x=>x.includes(s(a.anchor)))+1:null;
   return {source:src,source_kind:'ORIGINAL_PUBLIC',available_fulltext:true,original_scope:'A6N-T1 public released paper',
     total_lines:lines.length,line_start:n1,line_end:Math.min(n2,lines.length),
     content:lines.slice(n1-1,n2).join('\n'),anchor_line:anchor||null,revision:ctx.revision};
 }
 function getDocument(a={}){
   const p=s(a.path);
   if(!(p==='ARBEITSSTAND.md'||p==='ERKENNTNISSE.md'||p==='FORSCHUNGSKARTE.md'||p==='README.md'||/^forschung\/B\d{2}\.md$/.test(p)||['forschung/FUNKTIONERBE.md','forschung/REGENERIERBARKEIT_HOEHERER_ORDNUNG.md'].includes(p)||/^erscheinungswelt\/[A-Za-z0-9_]+\.md$/.test(p)||/^erkenntnisse\/PGKM-\d{3}\.md$/.test(p)||p==='beweise/A6N-T1_SRC-078.md'))fail('Document not public allowlisted','NOT_FOUND');
   const data=file(bundle,p).content;
   const lines=data.split(/\r?\n/),start=a.line_start==null?1:Number(a.line_start),max=a.max_lines==null?200:Number(a.max_lines);
   if(!Number.isInteger(start)||start<1||!Number.isInteger(max)||max<1||max>500)fail('Invalid line arguments');
   return {path:p,total_lines:lines.length,line_start:start,line_end:Math.min(lines.length,start+max-1),
     content:lines.slice(start-1,start+max-1).join('\n'),source_kind:p.startsWith('beweise/')?'ORIGINAL_PUBLIC':'PUBLIC_DERIVED_VIEW',
     revision:ctx.revision};
 }
 function getAxes(a={}){
   const k=a.kind||'all',v=k==='area'?idx.axes.areas:k==='mirror'?idx.axes.contrast_axes:[...idx.axes.areas,...idx.axes.contrast_axes];
   if(!['all','area','mirror'].includes(k))fail('Invalid axis kind');
   let result=a.id?v.filter(x=>x.id===a.id):v;
   if(a.query)result=result.filter(x=>score(JSON.stringify(x),a.query)>0);
   return {items:result,source_kind:'EDITORIAL_AXES',revision:ctx.revision};
 }
 function getAppearance(a={}) {if(a.include_candidates)return idx.comparison.get('pgk_get_appearance_anchor',a);if(a.id)fail('Empirical record not registered','NOT_FOUND');
   return {records:page(idx.appearance,a),source_kind:'PUBLIC_EMPTY_APPEARANCE_REGISTRY',exploratory_anchors_available:idx.comparison.anchors.length,exploratory_analogy_candidates_available:idx.comparison.cmp.length,revision:ctx.revision};}
 function getBridge(a={}) {if(a.id)fail('Bridge record not registered','NOT_FOUND');
   return {records:page(idx.bridges,a),source_kind:'PUBLIC_EMPTY_BRIDGE_REGISTRY',exploratory_comparisons_available:idx.comparison.cmp.length,revision:ctx.revision,note:'Use pgk_get_appearance_comparison for exploratory analogies; these are NOT registered empirical bridges.'};}
 function validateDraft(a={}){
   const draft=a.draft;
   if(!draft||typeof draft!=='object'||Array.isArray(draft))fail('Draft must be object');
   if(JSON.stringify(draft).length>30000)fail('Draft too large');
   const issues=[];
   function check(x,type){
     if(!x||typeof x!=='object'||Array.isArray(x)){issues.push(type+': invalid object');return;}
     if(!s(x.id).trim())issues.push(type+': missing id');
     if(type==='claim'){
       if(!s(x.aussage).trim())issues.push(type+': missing aussage');
       if(!idx.mmap.has(x.module_id))issues.push(type+': module not registered');
       if(!Array.isArray(x.source_ids))issues.push(type+': source_ids must be array');
       else for(const id of x.source_ids)if(!idx.smap.has(id))issues.push(type+': unknown source '+id);
     }
     if(type==='relation'){
       if(!idx.cmap.has(x.from)&&!idx.cmap.has(x.von))issues.push(type+': source claim missing');
       if(!idx.cmap.has(x.to)&&!idx.cmap.has(x.nach))issues.push(type+': target claim missing');
     }
   }
   const type=a.type||'batch';
   if(type==='batch'){
     for(const key of ['module','claim','relation','source','appearance','bridge'])
       for(const x of (Array.isArray(draft[key+'s'])?draft[key+'s']:[]))check(x,key);
   }else check(draft,type);
   return {schema_valid:issues.length===0,referentially_valid:issues.length===0,issues,
     publication_ready:false,scientific_approval:false,release_approved:false,
     note:'Technical preflight only. Open hypotheses and justified estimates are legitimate but not auto-approved.'};
 }
 function compareTo(oldBundle,options={}){
   if(!oldBundle||oldBundle.schema!==bundle.schema)fail('Need compatible older public snapshot');
   const keys=['daten/claims.json','daten/relations.json','daten/module.json','daten/sources.json',
     'daten/research_findings.json','daten/research_state.json','daten/evidence_passports.json',
     'daten/review_relations.json','daten/coverage.json','daten/axes.json',
     'daten/appearance.json','daten/bridges.json',
     'erscheinungswelt/daten/vergleich_kandidaten_v02.json','erscheinungswelt/daten/ew_anker_v02.json',
     'erscheinungswelt/daten/modell_luecken_v02.json','erscheinungswelt/daten/erganzende_forschungsfronten_v02.json'];
   const lists={
     'daten/claims.json':'claims','daten/relations.json':'relations','daten/module.json':'modules',
     'daten/sources.json':'sources','daten/research_findings.json':'findings',
     'daten/evidence_passports.json':'passports','daten/review_relations.json':'relations',
     'daten/coverage.json':'items',
     'erscheinungswelt/daten/vergleich_kandidaten_v02.json':'items',
     'erscheinungswelt/daten/ew_anker_v02.json':'anchors',
     'erscheinungswelt/daten/modell_luecken_v02.json':'gaps',
     'erscheinungswelt/daten/erganzende_forschungsfronten_v02.json':'candidates',
   };
   const max=options.limit??100;
   if(!Number.isInteger(max)||max<1||max>200)fail('compare limit must be 1..200');
   const changes=[];
   for(const k of keys){
     const prev=oldBundle.files[k]?.sha256||null,curr=bundle.files[k]?.sha256||null;
     if(prev===curr)continue;
     const entry={path:k,previous_sha256:prev,current_sha256:curr};
     if(lists[k] && bundle.files[k]){
       const a=oldBundle.files[k]?JSON.parse(oldBundle.files[k].content)[lists[k]]:[];
       const b=JSON.parse(bundle.files[k].content)[lists[k]];
       const before=new Map((a||[]).map(x=>[x.id||x.finding_id,x]));
       const after=new Map((b||[]).map(x=>[x.id||x.finding_id,x]));
       const delta={added:[],removed:[],modified:[]};
       for(const id of [...new Set([...before.keys(),...after.keys()])].sort()){
         if(!before.has(id))delta.added.push(id);
         else if(!after.has(id))delta.removed.push(id);
         else if(JSON.stringify(before.get(id))!==JSON.stringify(after.get(id)))delta.modified.push(id);
       }
       entry.record_delta={counts:Object.fromEntries(Object.entries(delta).map(([k,v])=>[k,v.length])),
          ids:Object.fromEntries(Object.entries(delta).map(([k,v])=>[k,v.slice(0,max)])),
          truncated:Object.fromEntries(Object.entries(delta).map(([k,v])=>[k,v.length>max]))};
     }
     changes.push(entry);
   }
   return {from_revision:options.baseline_revision||null,to_revision:ctx.revision,changed:changes,
     scientific_implication:'NONE_AUTOMATICALLY',source_kind:'VERSIONED_PUBLIC_DIFF'};
 }

 const actions={pgk_status:status,pgk_search:search,pgk_get_module:getModule,
   pgk_get_section:getSection,pgk_get_claim:getClaim,pgk_get_relations:getRelations,
   pgk_get_source:getSource,pgk_get_document:getDocument,pgk_find_related:search,pgk_get_topic_relations:getTopicRelations,
   pgk_validate_draft:validateDraft,pgk_get_axes:getAxes,pgk_get_appearance:getAppearance,
   pgk_get_bridge:getBridge,pgk_get_research_record:getResearchRecord,
   ...Object.fromEntries(COMPARISON_TOOLS.map(tool=>[tool.name,a=>idx.comparison.get(tool.name,{...a})]))};
 return {bundle,context:ctx,call(name,args={}){if(!actions[name])fail('Unknown tool');return actions[name](args);},
   compareTo};
}
