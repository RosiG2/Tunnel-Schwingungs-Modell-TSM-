/* Public exploratory comparison layer. This is an analogy and research-navigation
 * index, not the approved empirical appearance/bridge registry. Read-only. */
const low=x=>String(x??'').normalize('NFKC').replace(/[\u2010-\u2015\u2212\uFE58\uFE63\uFF0D]/g,'-').toLocaleLowerCase('de-DE');
const data=(bundle,p)=>{const f=bundle.files[p];if(!f)throw new Error('Public comparison file unavailable: '+p);return JSON.parse(f.content);};
function lim(a,k,d=20){const x=a?.[k]??d;if(!Number.isInteger(x)||x<(k==='limit'?1:0)||x>(k==='limit'?100:100000))throw new Error(k+' invalid');return x;}
const paging=(rows,a)=>{const offset=lim(a,'offset',0),limit=lim(a,'limit',20);return {total:rows.length,offset,limit,has_more:offset+limit<rows.length,items:rows.slice(offset,offset+limit)};};
const matches=(value,q)=>!q||low(value).includes(low(q));
export const COMPARISON_TOOLS=[
{name:'pgk_get_appearance_comparison',description:'Read individual or paginated exploratory PGK↔appearance analogies (590 records). IDs are existing PGK references. NO scientific confirmation; separate from official bridge register.',inputSchema:{type:'object',properties:{id:{type:'string'},anker_id:{type:'string'},referenztyp:{type:'string'},query:{type:'string'},offset:{type:'integer',minimum:0},limit:{type:'integer',minimum:1,maximum:100},revision:{type:'string',description:'Optional exact 40-hex Git commit'}}}},
{name:'pgk_get_appearance_anchor',description:'Read 16 outside scientific/methodological comparison anchors, their source links and comparison limits; these do not validate PGK.',inputSchema:{type:'object',properties:{id:{type:'string'},query:{type:'string'},offset:{type:'integer',minimum:0},limit:{type:'integer',minimum:1,maximum:100},revision:{type:'string'}}}},
{name:'pgk_get_model_gap',description:'Read 20 identified model-to-observation gaps with proposed observables and follow-up tasks. Model gaps are open research tasks.',inputSchema:{type:'object',properties:{id:{type:'string'},query:{type:'string'},offset:{type:'integer',minimum:0},limit:{type:'integer',minimum:1,maximum:100},revision:{type:'string'}}}},
{name:'pgk_get_research_extension',description:'Read two distinct additional research directions: inherited outside roles and higher-order regeneration (theoretical, not native PASS).',inputSchema:{type:'object',properties:{id:{type:'string'},query:{type:'string'},offset:{type:'integer',minimum:0},limit:{type:'integer',minimum:1,maximum:100},revision:{type:'string'}}}}
];
export function makeComparisonApi(bundle,ctx){
 const cmp=data(bundle,'erscheinungswelt/daten/vergleich_kandidaten_v02.json').items;
 const anchors=data(bundle,'erscheinungswelt/daten/ew_anker_v02.json').anchors;
 const gaps=data(bundle,'erscheinungswelt/daten/modell_luecken_v02.json').gaps;
 const extras=data(bundle,'erscheinungswelt/daten/erganzende_forschungsfronten_v02.json').candidates;
 const types={pgk_get_appearance_comparison:[cmp,'PUBLIC_EXPLORATORY_ANALOGY_NOT_TESTED'],pgk_get_appearance_anchor:[anchors,'EXTERNAL_OBSERVATION_OR_METHOD_ANCHOR_NOT_PGK_VALIDATION'],pgk_get_model_gap:[gaps,'PUBLIC_OPEN_MODEL_GAP'],pgk_get_research_extension:[extras,'PUBLIC_THEORETICAL_OR_SOURCE_MEDIATED_RESEARCH']};
 const ix=Object.fromEntries(Object.entries(types).map(([k,[rows]])=>[k,new Map(rows.map(r=>[r.id,r]))]));
 function get(name,a={}){
  const [rows,source_kind]=types[name]||[];if(!rows)throw new Error('Unknown comparison tool');
  if(a.id){const r=ix[name].get(a.id);if(!r)throw new Error('Comparison record not found: '+a.id);
    return {record:r,source_kind,revision:ctx.revision,scientific_confirmation_not_implied:true,from_official_bridge_registry:false};}
  const selected=rows.filter(r=>matches(JSON.stringify(r),a.query) &&
      (name!=='pgk_get_appearance_comparison'||((!a.anker_id||r.anker_ids?.includes(a.anker_id))&&(!a.referenztyp||r.referenztyp===a.referenztyp))));
  const compact=selected.map(r=>name==='pgk_get_appearance_comparison'?{id:r.id,referenztyp:r.referenztyp,anker_ids:r.anker_ids,anschlusstyp:r.anschlusstyp,individueller_nachweis:r.individueller_nachweis,preview:String(r.kerninhalt||'').slice(0,240)}:r);
  return {records:paging(compact,a),source_kind,revision:ctx.revision,scientific_confirmation_not_implied:true,from_official_bridge_registry:false};
 }
 return {get,cmp,anchors,gaps,extras};
}
