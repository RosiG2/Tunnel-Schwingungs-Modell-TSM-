/** Deterministische Recherchefunktionen für den öffentlichen Theorieatlas.
 *  Keine LLM-Analysen; keine privaten Quellen; keine externen Suchdienste.
 */
export type Entry = {
  id: string;
  title: string;
  category: string;
  status: string;
  last_reviewed: string;
  note?: string;
  library?: string;
  source_scope?: string;
  related_ids?: string[];
};
export type Index = { title: string; edition: string; entries: Entry[] };

export const normalize = (text: string): string =>
  text.replace(/ä/g,'ae').replace(/Ä/g,'Ae').replace(/ö/g,'oe').replace(/Ö/g,'Oe')
    .replace(/ü/g,'ue').replace(/Ü/g,'Ue').replace(/ß/g,'ss')
    .normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ').trim();

const stopwords = new Set([
  'der','die','das','des','den','dem','ein','eine','einer','einem','und','oder','im','in',
  'auf','mit','von','für','fuer','bei','aus','wie','warum','welche','welcher','was','zu','zum','zur',
  'ist','sind','wird','werden','kann','können','koennen','nicht','noch','als','über','ueber',
  'durch','gegen','zwischen','theorie','luhmann','atlas','nach','vor','am','an','sich'
]);

function tokens(query: string): string[] {
  return [...new Set(normalize(query).split(' ').filter(x => x.length >= 3 && !stopwords.has(x)))];
}

function countMatches(source: string, word: string): number {
  const hay = ` ${normalize(source)} `;
  const needle = ` ${word} `;
  let result=0, from=0;
  while ((from=hay.indexOf(needle,from))!==-1 && result<3) {result++;from+=needle.length;}
  return result;
}

function shortExcerpt(body: string, terms: string[], max=280): string | null {
  const flat=body.replace(/\s+/g,' ').trim();
  // Position is measured in the original text, not in a diacritic-stripped copy.
  // Thus an umlaut never shifts a citation excerpt to unrelated text.
  const word=/[\p{L}\p{N}]+/gu;
  let pos=-1;
  for(const m of flat.matchAll(word)){
    if(terms.includes(normalize(m[0]))){ pos=m.index; break; }
  }
  if(pos<0)return null;
  const start=Math.max(0,pos-90),end=Math.min(flat.length,start+max);
  return `${start?'…':''}${flat.slice(start,end)}${end<flat.length?'…':''}`;
}

export function searchCorpus(index: Index, bodies: Map<string,string>, query: string, limit=6) {
  const terms=tokens(query);
  if (!terms.length) return {query,edition:index.edition,results:[],scanned:bodies.size,incomplete:bodies.size<index.entries.length};
  const results=index.entries.map(e=>{
    const title=normalize(e.title), id=normalize(e.id.replaceAll('-',' '));
    const note=e.note||'', body=bodies.get(e.id)||'';
    let score=0;
    const matched:string[]=[];
    for(const term of terms){
      const a=countMatches(title,term),b=countMatches(id,term),c=countMatches(note,term),d=countMatches(body,term);
      if(a) {score+=10; matched.push(`Titel:${term}`);}
      if(b) {score+=4;matched.push(`ID:${term}`);}
      if(c) {score+=Math.min(3,c)*2;matched.push(`Register:${term}`);}
      if(d) {score+=Math.min(2,d);matched.push(`Text:${term}`);}
    }
    if(terms.length>1 && normalize(body).includes(terms.join(' '))) score+=4;
    const excerpt=shortExcerpt(body,terms);
    return {id:e.id,title:e.title,library:e.library||null,status:e.status,last_reviewed:e.last_reviewed,
      source_scope:e.source_scope||null,score,matched_fields:matched,
      excerpt,excerpt_source:excerpt?'article_text':null};
  }).filter(e=>e.score>0).sort((a,b)=>b.score-a.score||a.id.localeCompare(b.id)).slice(0,Math.max(1,Math.min(10,limit)));
  return {query,edition:index.edition,results,scanned:bodies.size,incomplete:bodies.size<index.entries.length};
}

export function getReferencePath(index: Index, id: string, depth=1, maxNodes=15) {
  const map=new Map(index.entries.map(e=>[e.id,e]));
  if(!map.has(id)) return null;
  const queue=[{id,step:0}];
  const visited=new Set([id]);
  const edges:{from:string;to:string;meaning:string}[]=[];
  const safeDepth=Math.max(1,Math.min(2,depth));
  const cap=Math.max(2,Math.min(30,maxNodes));
  while(queue.length){
    const current=queue.shift()!;
    if(current.step>=safeDepth)continue;
    const source=map.get(current.id)!;
    const outbound=(source.related_ids||[]).filter(r=>map.has(r));
    const inbound=index.entries.filter(e=>(e.related_ids||[]).includes(current.id)).map(e=>e.id);
    for(const dest of outbound){
      if(!edges.some(e=>e.from===current.id&&e.to===dest))edges.push({from:current.id,to:dest,meaning:'editorial_related_id'});
    }
    for(const from of inbound){
      if(!edges.some(e=>e.from===from&&e.to===current.id))edges.push({from,to:current.id,meaning:'editorial_related_id'});
    }
    for(const next of [...outbound,...inbound]){
      if(!visited.has(next) && visited.size<cap){visited.add(next);queue.push({id:next,step:current.step+1});}
    }
  }
  const nodes=[...visited].map(i=>{
    const e=map.get(i)!;
    return {id:e.id,title:e.title,library:e.library||null,status:e.status,last_reviewed:e.last_reviewed,source_scope:e.source_scope||null};
  });
  return {start_id:id,edition:index.edition,depth:safeDepth,nodes,edges:edges.filter(e=>visited.has(e.from)&&visited.has(e.to)),
    caveat:'related_ids sind redaktionelle Lektürehinweise, keine geprüften Behauptungen über begriffliche oder kausale Beziehungen.'};
}
