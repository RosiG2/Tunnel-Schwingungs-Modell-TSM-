import { McpServer } from "@modelcontextprotocol/server";
import { createMcpHandler } from "agents/mcp/server";
import { z } from "zod";
import { searchCorpus, getReferencePath, type Index } from "./recherche";

type Env = { KNOWLEDGE_ROOT: string; OPENAI_CHALLENGE?: string };
const errorText=(reason:string)=>({content:[{type:"text" as const,text:reason}],isError:true});

async function readPublicText(url:string,maxBytes=240_000):Promise<string>{
  const res=await fetch(url,{headers:{"Accept":"text/plain, application/json"},redirect:"manual"});
  if(!res.ok)throw new Error(`Öffentliche Quelle nicht erreichbar: HTTP ${res.status}`);
  const declared=Number(res.headers.get('content-length')||'0');
  if(declared>maxBytes)throw new Error('Datei über Größengrenze');
  const body=await res.text();
  if(new TextEncoder().encode(body).length>maxBytes)throw new Error('Datei über Größengrenze');
  return body;
}
async function indexFor(root:string):Promise<Index>{
  const index=JSON.parse(await readPublicText(`${root}/index.json`,64_000));
  if(!index||typeof index.title!=='string'||typeof index.edition!=='string'||!Array.isArray(index.entries))throw new Error('Ungültiges Registerformat');
  if(index.entries.length>35)throw new Error('Register zu groß für den derzeitigen Volltext-Recherchepfad');
  const seen=new Set<string>();
  for(const e of index.entries){
    if(typeof e.id!=='string'||!/^[a-z0-9-]{1,64}$/.test(e.id)||seen.has(e.id)||typeof e.title!=='string')throw new Error('Ungültige oder doppelte Artikelkennung im Register');
    if(e.related_ids!==undefined && (!Array.isArray(e.related_ids)||e.related_ids.some((r:unknown)=>typeof r!=='string'|| !/^[a-z0-9-]{1,64}$/.test(r))))throw new Error('Ungültige Querverweise im Register');
    seen.add(e.id);
  }
  for(const e of index.entries){for(const id of (e.related_ids||[])){if(!seen.has(id))throw new Error('Unbekannte Querverweis-ID im Register');}}
  return index as Index;
}
function makeServer(root:string){
  const server=new McpServer({name:'luhmann-wissensbruecke',version:'0.2.1'});
  server.registerTool('luhmann_wissensindex',{
    description:'Liest das aktuelle öffentliche Luhmann-Register mit Edition, registrierten Artikelkennungen, redaktionellen Statusangaben und Verweisen.',
    inputSchema:{},annotations:{readOnlyHint:true,openWorldHint:true,destructiveHint:false}
  },async()=>{
    try {const index=await indexFor(root);return {content:[{type:'text' as const,text:JSON.stringify({...index,source:`${root}/index.json`},null,2)}]};}
    catch(e){return errorText(String(e));}
  });
  server.registerTool('luhmann_wissenseintrag',{
    description:'Liest einen im aktuellen Register nachgewiesenen öffentlichen Atlasbeitrag samt Metadaten und Quell-URL; kein beliebiger Dateiabruf.',
    inputSchema:{id:z.string().min(1).max(64).regex(/^[a-z0-9-]+$/)},
    annotations:{readOnlyHint:true,openWorldHint:true,destructiveHint:false}
  },async({id})=>{
    try{
      const index=await indexFor(root);
      const entry=index.entries.find(e=>e.id===id);
      if(!entry)return errorText('Eintrag existiert nicht im veröffentlichten Register');
      const url=`${root}/entries/${id}.md`;
      const content=await readPublicText(url);
      return {content:[{type:'text' as const,text:JSON.stringify({metadata:entry,edition:index.edition,source:url,article_markdown:content},null,2)}]};
    }catch(e){return errorText(String(e));}
  });
  server.registerTool('luhmann_themenrecherche',{
    description:'Sucht eine inhaltliche Fragestellung in den aktuell registrierten Atlasbeiträgen und liefert sortierte Fundstellen mit kurzen Ausschnitten, Quell-URLs, Editionsangaben und Quellenstatus. Keine Recherche außerhalb des Atlas, keine Primärtextverifikation.',
    inputSchema:{query:z.string().min(3).max(180),max_results:z.number().int().min(1).max(10).optional()},
    annotations:{readOnlyHint:true,openWorldHint:true,destructiveHint:false}
  },async({query,max_results})=>{
    try{
      const index=await indexFor(root),contents=new Map<string,string>(),failures:string[]=[];
      // Höchstens 35 registrierte, öffentlich konfigurierte Dateien; keine nutzerkontrollierten URLs.
      for(let from=0;from<index.entries.length;from+=6){
        await Promise.all(index.entries.slice(from,from+6).map(async e=>{
          try{contents.set(e.id,await readPublicText(`${root}/entries/${e.id}.md`));}
          catch{failures.push(e.id);}
        }));
      }
      const results=searchCorpus(index,contents,query,max_results??6);
      const enriched={...results,results:results.results.map(r=>({...r,source:`${root}/entries/${r.id}.md`})),source:`${root}/index.json`,unavailable_ids:failures};
      return {content:[{type:'text' as const,text:JSON.stringify(enriched,null,2)}]};
    }catch(e){return errorText(String(e));}
  });
  server.registerTool('luhmann_bezugspfad',{
    description:'Zeigt zu einer registrierten Artikelkennung die im aktuellen Register explizit angegebenen Querverweise und eingehenden Beziehungen. Verweiskanten sind redaktionelle Lektürehinweise, keine Beweise.',
    inputSchema:{id:z.string().min(1).max(64).regex(/^[a-z0-9-]+$/),depth:z.number().int().min(1).max(2).optional()},
    annotations:{readOnlyHint:true,openWorldHint:true,destructiveHint:false}
  },async({id,depth})=>{
    try{
      const index=await indexFor(root),graph=getReferencePath(index,id,depth??1);
      if(!graph)return errorText('Eintrag existiert nicht im veröffentlichten Register');
      return {content:[{type:'text' as const,text:JSON.stringify({...graph,source:`${root}/index.json`},null,2)}]};
    }catch(e){return errorText(String(e));}
  });
  return server;
}
export default {
  fetch(request:Request,env:Env,ctx:ExecutionContext){
    const path=new URL(request.url).pathname;
    if(path==='/.well-known/openai-apps-challenge')return env.OPENAI_CHALLENGE
      ? new Response(env.OPENAI_CHALLENGE,{headers:{'content-type':'text/plain; charset=utf-8','cache-control':'no-store'}})
      : new Response('Not configured',{status:404});
    if(path==='/')return new Response('Luhmann-Wissensbruecke | MCP: /mcp | Nur Lesezugriff',{headers:{'content-type':'text/plain; charset=utf-8'}});
    if(path!=='/mcp')return new Response('Not found',{status:404});
    const root=env.KNOWLEDGE_ROOT.replace(/\/$/,'');
    if(!root.startsWith('https://raw.githubusercontent.com/'))return new Response('Invalid source configuration',{status:500});
    return createMcpHandler(()=>makeServer(root))(request,env,ctx);
  }
} satisfies ExportedHandler<Env>;
