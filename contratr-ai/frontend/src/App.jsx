import { useState, useEffect, useRef, useCallback } from "react";
import * as api from "./services/api.js";

const F = "'DM Sans', sans-serif";
const riskColors = {
  critical: { bg: "rgba(239,68,68,0.1)", dot: "#EF4444", label: "Crítico" },
  high: { bg: "rgba(245,158,11,0.1)", dot: "#F59E0B", label: "Alto" },
  medium: { bg: "rgba(234,179,8,0.1)", dot: "#EAB308", label: "Médio" },
  low: { bg: "rgba(16,185,129,0.1)", dot: "#10B981", label: "Conforme" },
};
const inp = { width:"100%",padding:"12px 16px",borderRadius:"10px",border:"1px solid #334155",background:"rgba(30,41,59,0.6)",color:"#E2E8F0",fontSize:"14px",fontFamily:F,outline:"none" };
const btn = (bg="#6366F1") => ({ padding:"10px 20px",borderRadius:"10px",border:"none",background:`linear-gradient(135deg,${bg},${bg}dd)`,color:"white",fontSize:"13px",fontWeight:700,cursor:"pointer",fontFamily:F });
const sevDot = { critical:"#EF4444", high:"#F59E0B", medium:"#EAB308", low:"#10B981" };

function ScoreGauge({ score }) {
  const [a, setA] = useState(0);
  const c2 = 2*Math.PI*54;
  useEffect(() => { let f,s=null; const r=(t)=>{if(!s)s=t;const p=Math.min((t-s)/1600,1);setA(Math.round((1-Math.pow(1-p,3))*score));if(p<1)f=requestAnimationFrame(r)};f=requestAnimationFrame(r);return()=>cancelAnimationFrame(f) }, [score]);
  const c = a<=30?"#10B981":a<=50?"#F59E0B":"#EF4444";
  return (<svg width="120" height="120" viewBox="0 0 120 120"><circle cx="60" cy="60" r="54" fill="none" stroke="#1E293B" strokeWidth="7"/><circle cx="60" cy="60" r="54" fill="none" stroke={c} strokeWidth="7" strokeLinecap="round" strokeDasharray={c2} strokeDashoffset={c2-(a/100)*c2} transform="rotate(-90 60 60)"/><text x="60" y="54" textAnchor="middle" fill={c} fontSize="28" fontWeight="800" fontFamily={F}>{a}</text><text x="60" y="72" textAnchor="middle" fill="#64748B" fontSize="10" fontFamily={F}>de 100</text></svg>);
}

function Header({ title, onBack, right }) {
  return (<div style={{padding:"14px 24px",display:"flex",alignItems:"center",justifyContent:"space-between",borderBottom:"1px solid #1E293B",background:"rgba(10,15,28,0.8)",position:"sticky",top:0,zIndex:10}}>
    <div style={{display:"flex",alignItems:"center",gap:"10px"}}>
      {onBack && <button onClick={onBack} style={{background:"rgba(51,65,85,0.5)",border:"1px solid #334155",color:"#94A3B8",padding:"6px 14px",borderRadius:"8px",fontSize:"12px",cursor:"pointer",fontFamily:F}}>← Voltar</button>}
      <div style={{width:"30px",height:"30px",borderRadius:"8px",background:"linear-gradient(135deg,#6366F1,#8B5CF6)",display:"flex",alignItems:"center",justifyContent:"center"}}><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M9 15l2 2 4-4"/></svg></div>
      <span style={{fontWeight:700,fontSize:"15px",color:"#F8FAFC"}}>ContratR.ai <span style={{color:"#64748B",fontWeight:400,fontSize:"12px"}}>— {title}</span></span>
    </div>
    {right}
  </div>);
}

// ═══ LOGIN ═══
function LoginScreen({ onLogin }) {
  const [email,setEmail]=useState(""); const [pass,setPass]=useState(""); const [error,setError]=useState(""); const [loading,setLoading]=useState(false);
  const submit = async()=>{ setLoading(true);setError(""); try{ await api.login(email,pass);onLogin() }catch(e){setError(e.message||"Credenciais inválidas")}finally{setLoading(false)} };
  return (<div style={{minHeight:"100vh",display:"flex",alignItems:"center",justifyContent:"center",background:"linear-gradient(160deg,#0A0F1C 0%,#0F172A 40%,#1A1040 100%)",padding:"20px"}}>
    <div style={{width:"100%",maxWidth:"400px"}}>
      <div style={{textAlign:"center",marginBottom:"32px"}}>
        <div style={{display:"inline-flex",alignItems:"center",gap:"10px",marginBottom:"8px"}}>
          <div style={{width:"40px",height:"40px",borderRadius:"10px",background:"linear-gradient(135deg,#6366F1,#8B5CF6)",display:"flex",alignItems:"center",justifyContent:"center"}}><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M9 15l2 2 4-4"/></svg></div>
          <h1 style={{margin:0,fontSize:"24px",fontWeight:800,fontFamily:F,color:"#F8FAFC"}}>Contra<span style={{color:"#818CF8"}}>tR</span><span style={{color:"#6366F1",fontSize:"14px",verticalAlign:"super"}}>.ai</span></h1>
        </div>
        <p style={{color:"#64748B",fontSize:"13px",fontFamily:F,margin:0}}>Painel do Operador Master</p>
      </div>
      <div style={{background:"rgba(15,23,42,0.7)",border:"1px solid #1E293B",borderRadius:"16px",padding:"28px"}}>
        <div style={{marginBottom:"16px"}}><label style={{display:"block",fontSize:"12px",color:"#94A3B8",marginBottom:"6px",fontFamily:F,fontWeight:600,textTransform:"uppercase",letterSpacing:"0.5px"}}>E-mail</label><input value={email} onChange={e=>setEmail(e.target.value)} placeholder="admin@contratr.ai" style={inp} onKeyDown={e=>e.key==="Enter"&&submit()}/></div>
        <div style={{marginBottom:"20px"}}><label style={{display:"block",fontSize:"12px",color:"#94A3B8",marginBottom:"6px",fontFamily:F,fontWeight:600,textTransform:"uppercase",letterSpacing:"0.5px"}}>Senha</label><input type="password" value={pass} onChange={e=>setPass(e.target.value)} placeholder="••••••••" style={inp} onKeyDown={e=>e.key==="Enter"&&submit()}/></div>
        {error && <p style={{color:"#EF4444",fontSize:"13px",margin:"0 0 12px",fontFamily:F}}>{error}</p>}
        <button onClick={submit} disabled={loading} style={{...btn(),width:"100%",opacity:loading?0.6:1}}>{loading?"Autenticando...":"Entrar"}</button>
      </div>
    </div>
  </div>);
}

// ═══ ADMIN PANEL ═══
function AdminPanel({ onAnalyze, onHistory, onLogout }) {
  const [companies,setCompanies]=useState([]); const [selId,setSelId]=useState(null); const [loading,setLoading]=useState(true);
  const [showAddComp,setShowAddComp]=useState(false); const [cName,setCName]=useState(""); const [cCnpj,setCCnpj]=useState(""); const [cSector,setCSector]=useState("");
  const [showAddPolicy,setShowAddPolicy]=useState(false); const [pRule,setPRule]=useState(""); const [pSev,setPSev]=useState("high"); const [pCat,setPCat]=useState("");
  const [showBulk,setShowBulk]=useState(false); const [bulkText,setBulkText]=useState(""); const [bulkResult,setBulkResult]=useState(null); const [bulkLoading,setBulkLoading]=useState(false);

  const loadCompanies=useCallback(async()=>{try{const d=await api.listCompanies();setCompanies(d.companies||[])}catch(e){console.error(e)}finally{setLoading(false)}},[]);
  useEffect(()=>{loadCompanies()},[loadCompanies]);
  const loadDetail=useCallback(async(id)=>{try{const d=await api.getCompany(id);setCompanies(p=>p.map(c=>c.company_id===id?d:c))}catch(e){console.error(e)}},[]);
  useEffect(()=>{if(selId)loadDetail(selId)},[selId,loadDetail]);
  const company=companies.find(c=>c.company_id===selId); const policies=company?.policies||[];

  const addCompany=async()=>{if(!cName.trim())return;try{const r=await api.createCompany({name:cName,cnpj:cCnpj,sector:cSector});setCompanies(p=>[...p,r]);setSelId(r.company_id);setCName("");setCCnpj("");setCSector("");setShowAddComp(false)}catch(e){alert(e.message)}};
  const addPolicy=async()=>{if(!pRule.trim()||!pCat.trim()||!selId)return;try{await api.addPolicy(selId,{rule:pRule,severity:pSev,category:pCat});await loadDetail(selId);setPRule("");setPCat("");setShowAddPolicy(false)}catch(e){alert(e.message)}};
  const delPolicy=async(pid)=>{try{await api.removePolicy(selId,pid);await loadDetail(selId)}catch(e){alert(e.message)}};
  const delCompany=async(cid)=>{try{await api.deleteCompany(cid);setCompanies(p=>p.filter(c=>c.company_id!==cid));if(selId===cid)setSelId(null)}catch(e){alert(e.message)}};

  // Bulk import
  const doBulkImport=async()=>{if(!bulkText.trim()||!selId)return;setBulkLoading(true);try{const r=await api.importPoliciesBulk(selId,bulkText);setBulkResult(r.policies||[])}catch(e){alert(e.message)}finally{setBulkLoading(false)}};
  const saveBulkPolicy=async(p)=>{try{await api.addPolicy(selId,{rule:p.rule,severity:p.severity,category:p.category});setBulkResult(prev=>prev.filter(x=>x.temp_id!==p.temp_id));await loadDetail(selId)}catch(e){alert(e.message)}};
  const updateBulkSeverity=(tempId,sev)=>{setBulkResult(prev=>prev.map(p=>p.temp_id===tempId?{...p,severity:sev}:p))};

  return (<div style={{minHeight:"100vh",background:"linear-gradient(160deg,#0A0F1C 0%,#0F172A 40%,#1A1040 100%)",fontFamily:F}}>
    <Header title="Painel Master" right={<button onClick={onLogout} style={{background:"rgba(239,68,68,0.1)",border:"1px solid rgba(239,68,68,0.2)",color:"#FCA5A5",padding:"6px 14px",borderRadius:"8px",fontSize:"12px",cursor:"pointer",fontFamily:F}}>Sair</button>}/>
    <div style={{maxWidth:"1000px",margin:"0 auto",padding:"24px 20px",display:"grid",gridTemplateColumns:"280px 1fr",gap:"20px"}}>
      {/* Sidebar */}
      <div>
        <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:"12px"}}>
          <h3 style={{margin:0,fontSize:"14px",fontWeight:700,color:"#F8FAFC"}}>Empresas</h3>
          <button onClick={()=>setShowAddComp(!showAddComp)} style={{background:"rgba(99,102,241,0.15)",border:"none",color:"#818CF8",width:"28px",height:"28px",borderRadius:"8px",cursor:"pointer",fontSize:"18px"}}>+</button>
        </div>
        {showAddComp&&(<div style={{background:"rgba(15,23,42,0.6)",border:"1px solid #334155",borderRadius:"12px",padding:"14px",marginBottom:"12px"}}>
          <input value={cName} onChange={e=>setCName(e.target.value)} placeholder="Nome da empresa" style={{...inp,marginBottom:"8px"}}/>
          <input value={cCnpj} onChange={e=>setCCnpj(e.target.value)} placeholder="CNPJ" style={{...inp,marginBottom:"8px"}}/>
          <input value={cSector} onChange={e=>setCSector(e.target.value)} placeholder="Setor" style={{...inp,marginBottom:"10px"}}/>
          <button onClick={addCompany} style={{...btn(),width:"100%"}}>Adicionar empresa</button>
        </div>)}
        {loading?<p style={{color:"#64748B",fontSize:"13px",textAlign:"center",padding:"20px"}}>Carregando...</p>:
        companies.length===0?<p style={{color:"#64748B",fontSize:"13px",textAlign:"center",padding:"20px"}}>Nenhuma empresa. Clique + para adicionar.</p>:
        <div style={{display:"flex",flexDirection:"column",gap:"6px"}}>{companies.map(c=>(<div key={c.company_id} onClick={()=>setSelId(c.company_id)} style={{padding:"12px 14px",borderRadius:"10px",cursor:"pointer",background:selId===c.company_id?"rgba(99,102,241,0.12)":"rgba(15,23,42,0.4)",border:`1px solid ${selId===c.company_id?"rgba(99,102,241,0.3)":"#1E293B"}`}}>
          <p style={{margin:0,fontSize:"13px",fontWeight:600,color:"#F8FAFC"}}>{c.name}</p>
          <p style={{margin:"2px 0 0",fontSize:"11px",color:"#64748B"}}>{c.sector||"Sem setor"} • {c.policies_count||0} política(s)</p>
        </div>))}</div>}
      </div>
      {/* Main */}
      <div>
        {!company?(<div style={{display:"flex",alignItems:"center",justifyContent:"center",height:"400px",color:"#475569",fontSize:"14px"}}>{loading?"Carregando...":"Selecione uma empresa"}</div>):(<>
          {/* Company header */}
          <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:"20px"}}>
            <div><h2 style={{margin:0,fontSize:"18px",fontWeight:700,color:"#F8FAFC"}}>{company.name}</h2><p style={{margin:"2px 0 0",fontSize:"12px",color:"#64748B"}}>{company.cnpj} • {company.sector}</p></div>
            <div style={{display:"flex",gap:"8px"}}>
              <button onClick={()=>onHistory(company)} style={{...btn("#0D9488")}}>Histórico</button>
              <button onClick={()=>onAnalyze(company)} style={btn()}>Analisar contrato</button>
              <button onClick={()=>delCompany(company.company_id)} style={{padding:"10px 14px",borderRadius:"10px",border:"1px solid rgba(239,68,68,0.3)",background:"rgba(239,68,68,0.08)",color:"#FCA5A5",fontSize:"12px",cursor:"pointer",fontFamily:F}}>Excluir</button>
            </div>
          </div>

          {/* Policies header */}
          <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:"12px"}}>
            <h3 style={{margin:0,fontSize:"14px",fontWeight:600,color:"#94A3B8"}}>Políticas internas ({policies.length})</h3>
            <div style={{display:"flex",gap:"8px"}}>
              <button onClick={()=>{setShowBulk(!showBulk);setShowAddPolicy(false);setBulkResult(null)}} style={{background:"rgba(139,92,246,0.1)",border:"1px solid rgba(139,92,246,0.2)",color:"#A78BFA",padding:"6px 14px",borderRadius:"8px",fontSize:"12px",cursor:"pointer",fontFamily:F,fontWeight:600}}>Import com IA</button>
              <button onClick={()=>{setShowAddPolicy(!showAddPolicy);setShowBulk(false)}} style={{background:"rgba(16,185,129,0.1)",border:"1px solid rgba(16,185,129,0.2)",color:"#6EE7B7",padding:"6px 14px",borderRadius:"8px",fontSize:"12px",cursor:"pointer",fontFamily:F,fontWeight:600}}>+ Adicionar</button>
            </div>
          </div>

          {/* Bulk import */}
          {showBulk&&(<div style={{background:"rgba(15,23,42,0.6)",border:"1px solid rgba(139,92,246,0.3)",borderRadius:"12px",padding:"16px",marginBottom:"14px"}}>
            <p style={{margin:"0 0 8px",fontSize:"12px",color:"#A78BFA",fontWeight:600}}>IMPORT INTELIGENTE COM IA</p>
            <p style={{margin:"0 0 10px",fontSize:"12px",color:"#94A3B8"}}>Cole o texto com as políticas da empresa. A IA vai separar cada política, categorizar e sugerir o nível de criticidade.</p>
            <textarea value={bulkText} onChange={e=>setBulkText(e.target.value)} placeholder="Cole aqui o documento de políticas da empresa...&#10;&#10;Ex: A multa rescisória não deve exceder 20% do valor do contrato. Todos os contratos devem ter reajuste pelo IPCA. O prazo de aviso para não-renovação deve ser de no máximo 30 dias..." rows={5} style={{...inp,resize:"vertical",marginBottom:"10px"}}/>
            <button onClick={doBulkImport} disabled={bulkLoading} style={{...btn("#8B5CF6"),opacity:bulkLoading?0.6:1}}>{bulkLoading?"Processando com IA...":"Analisar políticas"}</button>

            {/* Bulk results - review */}
            {bulkResult&&bulkResult.length>0&&(<div style={{marginTop:"14px"}}>
              <p style={{fontSize:"13px",color:"#A78BFA",fontWeight:600,margin:"0 0 10px"}}>{bulkResult.length} política(s) identificadas — revise a severidade e salve:</p>
              {bulkResult.map(p=>(<div key={p.temp_id} style={{display:"flex",alignItems:"center",gap:"10px",padding:"12px",background:"rgba(30,41,59,0.5)",border:"1px solid #334155",borderRadius:"8px",marginBottom:"8px"}}>
                <div style={{flex:1}}>
                  <div style={{display:"flex",alignItems:"center",gap:"6px",marginBottom:"4px"}}>
                    <span style={{fontSize:"10px",fontWeight:700,padding:"2px 8px",borderRadius:"4px",background:`${sevDot[p.severity]||"#64748B"}20`,color:sevDot[p.severity]||"#64748B",textTransform:"uppercase"}}>{riskColors[p.severity]?.label||p.severity}</span>
                    <span style={{fontSize:"11px",color:"#64748B"}}>{p.category}</span>
                  </div>
                  <p style={{margin:0,fontSize:"12px",color:"#CBD5E1",lineHeight:1.5}}>{p.rule}</p>
                  {p.reasoning&&<p style={{margin:"4px 0 0",fontSize:"11px",color:"#64748B",fontStyle:"italic"}}>{p.reasoning}</p>}
                </div>
                <select value={p.severity} onChange={e=>updateBulkSeverity(p.temp_id,e.target.value)} style={{...inp,width:"100px",fontSize:"11px",padding:"6px 8px"}}>
                  <option value="critical">Crítico</option><option value="high">Alto</option><option value="medium">Médio</option><option value="low">Baixo</option>
                </select>
                <button onClick={()=>saveBulkPolicy(p)} style={{...btn("#10B981"),padding:"6px 12px",fontSize:"11px"}}>Salvar</button>
              </div>))}
            </div>)}
            {bulkResult&&bulkResult.length===0&&<p style={{marginTop:"10px",fontSize:"13px",color:"#10B981"}}>Todas as políticas foram salvas!</p>}
          </div>)}

          {/* Add single policy */}
          {showAddPolicy&&(<div style={{background:"rgba(15,23,42,0.6)",border:"1px solid #334155",borderRadius:"12px",padding:"16px",marginBottom:"14px"}}>
            <textarea value={pRule} onChange={e=>setPRule(e.target.value)} placeholder="Descreva a regra" rows={2} style={{...inp,resize:"vertical",marginBottom:"10px"}}/>
            <div style={{display:"flex",gap:"10px",marginBottom:"10px"}}>
              <input value={pCat} onChange={e=>setPCat(e.target.value)} placeholder="Categoria" style={{...inp,flex:1}}/>
              <select value={pSev} onChange={e=>setPSev(e.target.value)} style={{...inp,flex:1,cursor:"pointer"}}><option value="critical">Crítico</option><option value="high">Alto</option><option value="medium">Médio</option><option value="low">Baixo</option></select>
            </div>
            <button onClick={addPolicy} style={btn("#10B981")}>Salvar política</button>
          </div>)}

          {/* Policies list */}
          <div style={{display:"flex",flexDirection:"column",gap:"8px"}}>
            {policies.map(p=>(<div key={p.policy_id} style={{display:"flex",alignItems:"flex-start",gap:"12px",padding:"14px 16px",background:"rgba(15,23,42,0.5)",border:"1px solid #1E293B",borderRadius:"10px"}}>
              <div style={{width:"8px",height:"8px",borderRadius:"50%",background:sevDot[p.severity]||"#64748B",marginTop:"5px",flexShrink:0}}/>
              <div style={{flex:1}}>
                <div style={{display:"flex",alignItems:"center",gap:"8px",marginBottom:"4px"}}>
                  <span style={{fontSize:"10px",fontWeight:700,padding:"2px 8px",borderRadius:"4px",background:`${sevDot[p.severity]||"#64748B"}20`,color:sevDot[p.severity]||"#64748B",textTransform:"uppercase"}}>{riskColors[p.severity]?.label||p.severity}</span>
                  <span style={{fontSize:"11px",color:"#64748B"}}>{p.category}</span>
                </div>
                <p style={{margin:0,fontSize:"13px",color:"#CBD5E1",lineHeight:1.5}}>{p.rule}</p>
              </div>
              <button onClick={()=>delPolicy(p.policy_id)} style={{background:"none",border:"none",color:"#475569",cursor:"pointer",fontSize:"16px",padding:"2px 6px"}}>✕</button>
            </div>))}
            {policies.length===0&&<p style={{color:"#475569",fontSize:"13px",textAlign:"center",padding:"40px"}}>Nenhuma política. Use "Import com IA" ou "+ Adicionar".</p>}
          </div>
        </>)}
      </div>
    </div>
  </div>);
}

// ═══ HISTORY ═══
function HistoryScreen({ company, onBack, onViewResult }) {
  const [analyses,setAnalyses]=useState([]); const [loading,setLoading]=useState(true); const [filter,setFilter]=useState("all");

  useEffect(()=>{
    const load=async()=>{try{const r=await api.getAnalysisHistory(company.company_id,filter==="all"?null:filter);setAnalyses(r.analyses||[])}catch(e){console.error(e)}finally{setLoading(false)}};
    load(); const interval=setInterval(load,10000); return()=>clearInterval(interval);
  },[company.company_id,filter]);

  const statusLabel={pending_upload:"Aguardando upload",extracting_text:"Extraindo texto...",text_extracted:"Texto extraído",analyzing_entities:"Analisando entidades...",entities_extracted:"Entidades extraídas",analyzing_with_ai:"Analisando com IA...",completed:"Concluído",error:"Erro"};
  const statusColor={completed:"#10B981",error:"#EF4444"};

  return (<div style={{minHeight:"100vh",background:"linear-gradient(160deg,#0A0F1C 0%,#0F172A 40%,#1A1040 100%)",fontFamily:F}}>
    <Header title={`Histórico — ${company.name}`} onBack={onBack}/>
    <div style={{maxWidth:"860px",margin:"0 auto",padding:"24px 20px"}}>
      <div style={{display:"flex",gap:"8px",marginBottom:"20px"}}>
        {["all","completed","error"].map(f=>(<button key={f} onClick={()=>{setFilter(f);setLoading(true)}} style={{padding:"6px 14px",borderRadius:"8px",border:"none",background:filter===f?"rgba(99,102,241,0.15)":"rgba(15,23,42,0.4)",color:filter===f?"#818CF8":"#64748B",fontSize:"12px",fontWeight:600,cursor:"pointer",fontFamily:F}}>{f==="all"?"Todos":f==="completed"?"Concluídos":"Erros"}</button>))}
      </div>
      {loading?<p style={{color:"#64748B",textAlign:"center",padding:"40px"}}>Carregando...</p>:
      analyses.length===0?<p style={{color:"#64748B",textAlign:"center",padding:"40px"}}>Nenhuma análise encontrada.</p>:
      <div style={{display:"flex",flexDirection:"column",gap:"10px"}}>
        {analyses.map(a=>(<div key={a.analysis_id} style={{display:"flex",alignItems:"center",gap:"14px",padding:"16px",background:"rgba(15,23,42,0.6)",border:"1px solid #1E293B",borderRadius:"12px",cursor:a.status==="completed"?"pointer":"default"}} onClick={()=>a.status==="completed"&&onViewResult(a.analysis_id,company)}>
          {/* Status indicator */}
          {a.status==="completed"?(<div style={{width:"44px",height:"44px",borderRadius:"50%",background:`${a.risk_score<=30?"rgba(16,185,129,0.15)":a.risk_score<=50?"rgba(245,158,11,0.15)":"rgba(239,68,68,0.15)"}`,display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0}}>
            <span style={{fontSize:"16px",fontWeight:800,color:a.risk_score<=30?"#10B981":a.risk_score<=50?"#F59E0B":"#EF4444"}}>{a.risk_score}</span>
          </div>):a.status==="error"?(<div style={{width:"44px",height:"44px",borderRadius:"50%",background:"rgba(239,68,68,0.15)",display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0}}><span style={{fontSize:"20px"}}>⚠️</span></div>
          ):(<div style={{width:"44px",height:"44px",borderRadius:"50%",border:"3px solid #1E293B",borderTopColor:"#6366F1",animation:"spin 1s linear infinite",flexShrink:0}}/>)}
          <div style={{flex:1}}>
            <p style={{margin:0,fontSize:"14px",fontWeight:600,color:"#F8FAFC"}}>{a.filename}</p>
            <div style={{display:"flex",alignItems:"center",gap:"8px",marginTop:"4px"}}>
              <span style={{fontSize:"11px",color:statusColor[a.status]||"#818CF8",fontWeight:600}}>{statusLabel[a.status]||a.status}</span>
              {a.progress>=0&&a.progress<100&&<span style={{fontSize:"11px",color:"#64748B"}}>{a.progress}%</span>}
              <span style={{fontSize:"11px",color:"#475569"}}>{new Date(a.created_at).toLocaleString("pt-BR")}</span>
            </div>
          </div>
          {a.status==="completed"&&<span style={{fontSize:"12px",color:"#64748B"}}>Ver →</span>}
        </div>))}
      </div>}
    </div>
    <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
  </div>);
}

// ═══ ANALYSIS FLOW ═══
function AnalysisFlow({ company, onBack, analysisIdToView }) {
  const [phase,setPhase]=useState(analysisIdToView?"polling":"upload");
  const [progress,setProgress]=useState({status:"",progress:0});
  const [result,setResult]=useState(null); const [error,setError]=useState(null);
  const [expandedClause,setExpandedClause]=useState(null);
  const fileRef=useRef(); const [dragging,setDragging]=useState(false);

  const statusLabels={requesting_upload:"Solicitando upload...",uploading:"Enviando PDF ao S3...",pending_upload:"Aguardando...",extracting_text:"Extraindo texto com Textract...",text_extracted:"Texto extraído!",analyzing_entities:"Identificando entidades com Comprehend...",entities_extracted:"Entidades extraídas!",analyzing_with_ai:"Analisando com Bedrock + políticas...",completed:"Concluído!",error:"Erro"};

  // If viewing existing result, poll it
  useEffect(()=>{
    if(!analysisIdToView)return;
    const poll=async()=>{try{
      const r=await api.pollAnalysis(analysisIdToView,(p)=>setProgress({status:p.status,progress:p.progress}));
      setResult(r);setPhase("results")
    }catch(e){setError(e.message);setPhase("error")}};
    poll();
  },[analysisIdToView]);

  const handleFile=async(f)=>{if(!f||f.type!=="application/pdf")return;setPhase("analyzing");setError(null);
    try{
      setProgress({status:"requesting_upload",progress:5});
      const upload=await api.requestUpload(f,company.company_id);
      setProgress({status:"uploading",progress:15});
      await api.uploadToS3(upload.upload_url,f);
      const final=await api.pollAnalysis(upload.analysis_id,(p)=>setProgress({status:p.status,progress:p.progress}));
      setResult(final);setPhase("results")
    }catch(e){setError(e.message||"Erro");setPhase("error")}
  };

  if(phase==="upload") return (<div style={{minHeight:"100vh",background:"linear-gradient(160deg,#0A0F1C 0%,#0F172A 40%,#1A1040 100%)",fontFamily:F}}>
    <Header title={`Análise — ${company.name}`} onBack={onBack}/>
    <div style={{display:"flex",flexDirection:"column",alignItems:"center",padding:"60px 20px"}}>
      <div style={{background:"rgba(99,102,241,0.08)",border:"1px solid rgba(99,102,241,0.2)",borderRadius:"12px",padding:"14px 20px",marginBottom:"32px",maxWidth:"500px"}}>
        <p style={{margin:0,fontSize:"13px",color:"#818CF8",lineHeight:1.6}}>Análise com base nas <strong>{company.policies?.length||0} políticas</strong> de {company.name}.</p>
      </div>
      <div onDragOver={e=>{e.preventDefault();setDragging(true)}} onDragLeave={()=>setDragging(false)} onDrop={e=>{e.preventDefault();setDragging(false);handleFile(e.dataTransfer.files[0])}} onClick={()=>fileRef.current.click()} style={{width:"100%",maxWidth:"460px",padding:"50px 40px",border:`2px dashed ${dragging?"#818CF8":"#334155"}`,borderRadius:"20px",cursor:"pointer",background:dragging?"rgba(99,102,241,0.06)":"rgba(15,23,42,0.6)",display:"flex",flexDirection:"column",alignItems:"center",gap:"14px",transition:"all 0.3s"}}>
        <input ref={fileRef} type="file" accept=".pdf" hidden onChange={e=>handleFile(e.target.files[0])}/>
        <div style={{width:"64px",height:"64px",borderRadius:"50%",background:"rgba(51,65,85,0.4)",display:"flex",alignItems:"center",justifyContent:"center"}}><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#64748B" strokeWidth="1.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg></div>
        <p style={{margin:0,color:"#E2E8F0",fontSize:"15px",fontWeight:600}}>Arraste o contrato PDF aqui</p>
        <p style={{margin:0,color:"#64748B",fontSize:"12px"}}>ou clique para selecionar</p>
      </div>
    </div>
  </div>);

  if(phase==="analyzing"||phase==="polling") return (<div style={{minHeight:"100vh",display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",background:"linear-gradient(160deg,#0A0F1C 0%,#0F172A 40%,#1A1040 100%)",fontFamily:F}}>
    <div style={{width:"70px",height:"70px",borderRadius:"50%",border:"3px solid #1E293B",borderTopColor:"#6366F1",animation:"spin 1s linear infinite",marginBottom:"28px"}}/><style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
    <h2 style={{color:"#F8FAFC",fontSize:"20px",fontWeight:700,margin:"0 0 12px"}}>Analisando contrato</h2>
    <p style={{color:"#818CF8",fontSize:"14px",margin:"0 0 8px",fontWeight:600}}>{statusLabels[progress.status]||progress.status}</p>
    <div style={{width:"320px",height:"6px",borderRadius:"3px",background:"#1E293B",marginTop:"16px"}}><div style={{width:`${Math.max(progress.progress,5)}%`,height:"100%",borderRadius:"3px",background:"linear-gradient(90deg,#6366F1,#8B5CF6)",transition:"width 0.5s"}}/></div>
    <p style={{color:"#475569",fontSize:"12px",marginTop:"8px"}}>{progress.progress}%</p>
  </div>);

  if(phase==="error") return (<div style={{minHeight:"100vh",display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",background:"linear-gradient(160deg,#0A0F1C 0%,#0F172A 40%,#1A1040 100%)",fontFamily:F}}>
    <div style={{background:"rgba(239,68,68,0.1)",border:"1px solid rgba(239,68,68,0.2)",borderRadius:"16px",padding:"32px",maxWidth:"460px",textAlign:"center"}}>
      <p style={{fontSize:"40px",margin:"0 0 12px"}}>⚠️</p><h2 style={{color:"#FCA5A5",fontSize:"18px",fontWeight:700,margin:"0 0 8px"}}>Erro na análise</h2>
      <p style={{color:"#94A3B8",fontSize:"13px",lineHeight:1.6,margin:"0 0 20px"}}>{error}</p>
      <div style={{display:"flex",gap:"10px",justifyContent:"center"}}><button onClick={()=>setPhase("upload")} style={btn()}>Tentar novamente</button><button onClick={onBack} style={{padding:"10px 20px",borderRadius:"10px",border:"1px solid #334155",background:"transparent",color:"#94A3B8",fontSize:"13px",cursor:"pointer",fontFamily:F}}>Voltar</button></div>
    </div>
  </div>);

  // Results
  const analysis=result?.analysis||{}; const clauses=analysis.clauses||[]; const score=analysis.score||result?.risk_score||0;
  const scoreLabel=analysis.score_label||(score<=30?"Baixo Risco":score<=50?"Médio Risco":score<=70?"Alto Risco":"Risco Crítico");

  return (<div style={{minHeight:"100vh",background:"linear-gradient(160deg,#0A0F1C 0%,#0F172A 40%,#1A1040 100%)",fontFamily:F,color:"#E2E8F0"}}>
    <Header title={company.name} onBack={onBack}/>
    <div style={{maxWidth:"860px",margin:"0 auto",padding:"24px 20px"}}>
      {/* Score */}
      <div style={{display:"grid",gridTemplateColumns:"130px 1fr",gap:"24px",background:"rgba(15,23,42,0.6)",border:"1px solid #1E293B",borderRadius:"16px",padding:"24px",marginBottom:"20px"}}>
        <div style={{display:"flex",flexDirection:"column",alignItems:"center",gap:"6px"}}><ScoreGauge score={score}/><span style={{fontSize:"12px",fontWeight:700,padding:"3px 12px",borderRadius:"20px",textTransform:"uppercase",color:score<=30?"#10B981":score<=50?"#F59E0B":"#EF4444",background:score<=30?"rgba(16,185,129,0.12)":score<=50?"rgba(245,158,11,0.12)":"rgba(239,68,68,0.12)"}}>{scoreLabel}</span></div>
        <div>
          <h2 style={{margin:"0 0 4px",fontSize:"16px",fontWeight:700,color:"#F8FAFC"}}>Resultado da Análise</h2>
          {analysis.policies_violated!==undefined&&(<div style={{display:"flex",gap:"16px",marginBottom:"12px"}}>
            <div style={{background:"rgba(239,68,68,0.08)",border:"1px solid rgba(239,68,68,0.2)",borderRadius:"8px",padding:"8px 14px"}}><p style={{margin:0,fontSize:"20px",fontWeight:800,color:"#EF4444"}}>{analysis.policies_violated}</p><p style={{margin:0,fontSize:"10px",color:"#FCA5A5",textTransform:"uppercase"}}>Políticas violadas</p></div>
            <div style={{background:"rgba(16,185,129,0.08)",border:"1px solid rgba(16,185,129,0.2)",borderRadius:"8px",padding:"8px 14px"}}><p style={{margin:0,fontSize:"20px",fontWeight:800,color:"#10B981"}}>{(analysis.policies_total||0)-(analysis.policies_violated||0)}</p><p style={{margin:0,fontSize:"10px",color:"#6EE7B7",textTransform:"uppercase"}}>Em conformidade</p></div>
          </div>)}
          <p style={{margin:0,fontSize:"13px",color:"#94A3B8",lineHeight:1.6}}>{analysis.summary||"Análise concluída."}</p>
        </div>
      </div>
      {/* Clauses */}
      {clauses.length>0&&(<><h3 style={{margin:"0 0 12px",fontSize:"14px",fontWeight:600,color:"#94A3B8"}}>Cláusulas ({clauses.length})</h3>
        <div style={{display:"flex",flexDirection:"column",gap:"10px"}}>{clauses.map((c,i)=>{const rc=riskColors[c.risk_level]||riskColors.medium;const isO=expandedClause===i;
          return (<div key={i} onClick={()=>setExpandedClause(isO?null:i)} style={{background:"rgba(15,23,42,0.6)",border:`1px solid ${isO?rc.dot+"44":"#1E293B"}`,borderRadius:"12px",padding:"16px 18px",cursor:"pointer",transition:"all 0.3s"}}>
            <div style={{display:"flex",alignItems:"center",justifyContent:"space-between"}}><div style={{display:"flex",alignItems:"center",gap:"10px"}}><div style={{width:"8px",height:"8px",borderRadius:"50%",background:rc.dot}}/><span style={{fontWeight:600,fontSize:"13px",color:"#F8FAFC"}}>{c.title}</span></div><span style={{fontSize:"10px",fontWeight:700,padding:"2px 8px",borderRadius:"5px",background:rc.bg,color:rc.dot,textTransform:"uppercase"}}>{rc.label}</span></div>
            {isO&&(<div style={{marginTop:"14px",display:"flex",flexDirection:"column",gap:"12px"}}>
              {c.original_text&&<div style={{background:"rgba(30,41,59,0.5)",borderRadius:"8px",padding:"12px",borderLeft:`3px solid ${rc.dot}`}}><p style={{margin:"0 0 2px",fontSize:"10px",color:"#64748B",fontWeight:600,textTransform:"uppercase"}}>Texto original</p><p style={{margin:0,fontSize:"12px",color:"#CBD5E1",lineHeight:1.5,fontStyle:"italic"}}>"{c.original_text}"</p></div>}
              {c.analysis&&<div><p style={{margin:"0 0 2px",fontSize:"10px",color:"#64748B",fontWeight:600,textTransform:"uppercase"}}>Análise da IA</p><p style={{margin:0,fontSize:"12px",color:"#94A3B8",lineHeight:1.5}}>{c.analysis}</p></div>}
              {c.policy_violated&&<div style={{background:"rgba(239,68,68,0.06)",border:"1px solid rgba(239,68,68,0.15)",borderRadius:"8px",padding:"12px"}}><p style={{margin:"0 0 2px",fontSize:"10px",color:"#EF4444",fontWeight:600,textTransform:"uppercase"}}>Política violada</p><p style={{margin:0,fontSize:"12px",color:"#FCA5A5",lineHeight:1.5}}>{c.policy_violated}</p></div>}
              {c.recommendation&&<div style={{background:"rgba(16,185,129,0.06)",border:"1px solid rgba(16,185,129,0.15)",borderRadius:"8px",padding:"12px"}}><p style={{margin:"0 0 2px",fontSize:"10px",color:"#10B981",fontWeight:600,textTransform:"uppercase"}}>Recomendação</p><p style={{margin:0,fontSize:"12px",color:"#A7F3D0",lineHeight:1.5}}>{c.recommendation}</p></div>}
            </div>)}
          </div>)})}</div></>)}
      {/* Financial risks */}
      {analysis.financial_risks?.length>0&&(<><h3 style={{margin:"20px 0 12px",fontSize:"14px",fontWeight:600,color:"#94A3B8"}}>Riscos financeiros</h3>
        <div style={{display:"flex",flexDirection:"column",gap:"8px"}}>{analysis.financial_risks.map((r,i)=>{const rc=riskColors[r.severity]||riskColors.medium;
          return (<div key={i} style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"14px 18px",borderRadius:"10px",background:"rgba(30,41,59,0.4)",borderLeft:`4px solid ${rc.dot}`}}><span style={{fontSize:"13px",color:"#E2E8F0"}}>{r.label}</span><span style={{fontSize:"18px",fontWeight:800,color:rc.dot}}>{r.estimated_value}</span></div>)})}</div></>)}
    </div>
  </div>);
}

// ═══ APP ROOT ═══
export default function App() {
  const [auth,setAuth]=useState(false); const [screen,setScreen]=useState("admin");
  const [selCompany,setSelCompany]=useState(null); const [viewAnalysisId,setViewAnalysisId]=useState(null);

  const logout=()=>{api.clearToken();setAuth(false);setScreen("admin");setSelCompany(null);setViewAnalysisId(null)};

  if(!auth) return <LoginScreen onLogin={()=>setAuth(true)}/>;

  if(screen==="history"&&selCompany) return <HistoryScreen company={selCompany} onBack={()=>{setScreen("admin");setSelCompany(null)}}
    onViewResult={(aid,comp)=>{setViewAnalysisId(aid);setSelCompany(comp);setScreen("analyze")}}/>;

  if(screen==="analyze"&&selCompany) return <AnalysisFlow company={selCompany} analysisIdToView={viewAnalysisId}
    onBack={()=>{setScreen("admin");setSelCompany(null);setViewAnalysisId(null)}}/>;

  return <AdminPanel
    onAnalyze={(c)=>{setSelCompany(c);setViewAnalysisId(null);setScreen("analyze")}}
    onHistory={(c)=>{setSelCompany(c);setScreen("history")}}
    onLogout={logout}/>;
}
