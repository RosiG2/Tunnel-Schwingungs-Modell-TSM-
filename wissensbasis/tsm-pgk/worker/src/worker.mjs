/* Stateless MCP Streamable HTTP, JSON responses, no GitHub writes.
 * 2025-11-25 compatibility and minimal 2026-07-28 no-session transport.
 */
import {TOOLS} from './public_core.mjs';
import {apiForRequest,loadPublication,sha256Bytes} from './loader.mjs';
const VERSION='0.8.4-open-rc1';
const JSON_HEADERS={'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'};
function jsonResult(x,status=200){return new Response(JSON.stringify(x),{status,headers:JSON_HEADERS});}
function jsonError(id,code,message,data){return {jsonrpc:'2.0',id,error:{code,message,...(data?{data}:{})}};}
function jsonOK(id,result){return {jsonrpc:'2.0',id,result};}
function methodAllowed(req,env){const origin=req.headers.get('Origin');if(!origin)return true;let allowed=(env?.ALLOWED_ORIGINS||'https://chatgpt.com,https://chat.openai.com').split(',').map(x=>x.trim());return allowed.includes(origin);}
function cleanArgs(x){return x&&typeof x==='object'&&!Array.isArray(x)?x:{};}
export async function handleRequest(request,env={},deps={}){
 const u=new URL(request.url),path=u.pathname;
 // OpenAI domain ownership verification. The token is supplied by the submission portal,
 // belongs to this MCP hostname, and must be returned as exact plain text.
 if(path==='/.well-known/openai-apps-challenge'){
   if(request.method!=='GET')return new Response('Method not allowed',{status:405,headers:{Allow:'GET'}});
   const token=typeof env?.OPENAI_CHALLENGE==='string'?env.OPENAI_CHALLENGE:'';
   return token
     ? new Response(token,{status:200,headers:{'Content-Type':'text/plain; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}})
     : new Response('Not configured',{status:404,headers:{'Cache-Control':'no-store'}});
 }
 if(!methodAllowed(request,env))return new Response('Forbidden Origin',{status:403});
 if(path==='/health'&&request.method==='GET')return jsonResult({name:'tsm-pgk-mcp',version:VERSION,status:'server_active',scientific_approval:false});
 if(path!=='/mcp')return new Response('Not found',{status:404});
 if(request.method==='GET'||request.method==='DELETE')return new Response('MCP stream/session endpoint not supported',{status:405,headers:{Allow:'POST'}});
 if(request.method!=='POST')return new Response('Method not allowed',{status:405,headers:{Allow:'POST'}});
 if(!request.headers.get('Content-Type')?.includes('application/json'))return jsonResult(jsonError(null,-32600,'Content-Type must be application/json'),415);
 // Keep a limit on submitted drafts and request payloads. No chat transcript or query logging.
 const body=await request.text();if(new TextEncoder().encode(body).length>64000)return jsonResult(jsonError(null,-32600,'Request body too large'),413);
 let rpc;try{rpc=JSON.parse(body);}catch{return jsonResult(jsonError(null,-32700,'Parse error'),400);}
 if(!rpc||rpc.jsonrpc!=='2.0'||typeof rpc.method!=='string'||Array.isArray(rpc))return jsonResult(jsonError(rpc?.id??null,-32600,'Invalid JSON-RPC request'),400);
 // Validate the additional 2026-07-28 transport headers when the modern protocol is selected.
 // Legacy 2025 clients retain their original request shape (no fabricated session).
 const protocolHeader=request.headers.get('MCP-Protocol-Version');
 if(protocolHeader && !['2025-11-25','2026-07-28'].includes(protocolHeader))
   return jsonResult(jsonError(rpc.id??null,-32022,'Unsupported protocol version',
       {supported:['2026-07-28','2025-11-25'],requested:protocolHeader}),400);
 if(protocolHeader==='2026-07-28'){
   const metaVersion=rpc.params?._meta?.['io.modelcontextprotocol/protocolVersion'];
   if(metaVersion!==protocolHeader || request.headers.get('Mcp-Method')!==rpc.method || (rpc.method==='tools/call' && request.headers.get('Mcp-Name')!==rpc.params?.name)){
     return jsonResult(jsonError(rpc.id??null,-32020,'HeaderMismatch: MCP-Protocol-Version, Mcp-Method and Mcp-Name must match JSON-RPC body'),400);
   }
 }
 if(!Object.prototype.hasOwnProperty.call(rpc,'id'))return new Response(null,{status:202});
 const id=rpc.id;
 if(rpc.method==='server/discover' && protocolHeader==='2026-07-28'){
   return jsonResult(jsonOK(id,{resultType:'complete',
      supportedVersions:['2026-07-28','2025-11-25'],capabilities:{tools:{}},
      _meta:{'io.modelcontextprotocol/serverInfo':{name:'tsm-pgk-research-mcp',version:VERSION}},
      instructions:'Read-only open PGK research memory. Scientific status is preserved; source originals are not inferred.',
      ttlMs:3600000,cacheScope:'public'}));
 }
 if(rpc.method==='initialize'){
   const selected='2025-11-25';
   return jsonResult(jsonOK(id,{protocolVersion:selected,capabilities:{tools:{listChanged:false}},serverInfo:{name:'tsm-pgk-research-mcp',version:VERSION},instructions:'Read-only public PGK research preview. Derived research summaries are not originals or scientific endorsements; estimates and alternative candidates are legitimate research.'}));
 }
 if(rpc.method==='ping')return jsonResult(jsonOK(id,{}));
 if(rpc.method==='tools/list')return jsonResult(jsonOK(id,{tools:TOOLS}));
 if(rpc.method!=='tools/call')return jsonResult(jsonError(id,-32601,'Unknown method'));
 const name=rpc.params?.name;
 if(!TOOLS.some(t=>t.name===name))return jsonResult(jsonError(id,-32601,'Unknown tool'));
 const args=cleanArgs(rpc.params?.arguments);
 try{
   const getApi=deps.apiForRequest||apiForRequest;
   const {api}=await getApi(env,args.revision||null);
   let result;
   if(name==='pgk_compare_versions'){
     if(!args.baseline_revision|| !/^[a-f0-9]{40}$/i.test(args.baseline_revision))
       throw Error('For the public view, baseline_revision must be a full earlier 40-character GitHub commit SHA');
     const load=deps.loadPublication||loadPublication;
     const old=await load(env,args.baseline_revision);
     result=api.compareTo(old.bundle,{baseline_revision:old.revision,limit:args.limit||100});
   }else result=api.call(name,args);
   return jsonResult(jsonOK(id,{content:[{type:'text',text:JSON.stringify(result)}],structuredContent:result,isError:false}));
 }catch(e){
   const code=e.kind==='NOT_FOUND'?'NOT_FOUND':e.kind==='INTEGRITY_ERROR'?'INTEGRITY_ERROR':'REQUEST_FAILED';
   return jsonResult(jsonOK(id,{content:[{type:'text',text:`${code}: ${e.message}`}],isError:true}));
 }
}
// Matches the sorted-key, compact JSON snapshots produced by build_publication.py.
function stableJson(x){if(Array.isArray(x))return '['+x.map(stableJson).join(',')+']';if(x&&typeof x==='object')return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+stableJson(x[k])).join(',')+'}';return JSON.stringify(x);}
export default {async fetch(request,env,ctx){return handleRequest(request,env);}};
