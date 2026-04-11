"use client";

import { useState, useEffect, useMemo, useRef } from "react";

const API = "http://localhost:8000";

interface Depute { id:string;prenom:string;nom:string;groupe:string;circonscription:string;photo_url:string; }
interface Parti { id:string;slug:string;nom:string;nom_court:string;couleur:string;nb_sieges:number;orientation:string;description:string; }
interface Ministre { nom:string;prenom:string;role:string;parti:string;rang:number;couleur:string;initiales:string;photo_url:string;description?:string; }

const ORDRE_POLITIQUE = ["LFI","GDR","ECO","SOC","NFP","LIOT","MODEM","ENS","REN","HOR","DR","LR","RN","NI"];
const COULEURS: Record<string,string> = {
  RN:"#003189",DR:"#0D47A1",LR:"#0D47A1",HOR:"#1565C0",ENS:"#FF6D00",REN:"#FF6D00",NFP:"#8B0000",
  MODEM:"#FF8F00",SOC:"#E91E63",ECO:"#2E7D32",LFI:"#B71C1C",GDR:"#C62828",LIOT:"#6A1B9A",NI:"#607D8B",
};
const normalize = (s:string) => s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"");
const c = (g:string) => COULEURS[g]??"#607D8B";

// ── Logo parti ────────────────────────────────────────────────────────────────
function LogoParti({partiId,nom,size=48,className=""}:{partiId:string;nom:string;size?:number;className?:string}) {
  const [err,setErr] = useState(false);
  const col = c(partiId);
  if(err) return (
    <div className={`flex items-center justify-center text-white font-black rounded-xl ${className}`}
      style={{width:size,height:size,background:col,fontSize:size*0.28}}>
      {partiId.slice(0,3)}
    </div>
  );
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={`${API}/proxy/logo/${partiId}`} alt={nom} onError={()=>setErr(true)}
      className={`object-contain rounded-xl bg-white ${className}`}
      style={{width:size,height:size,padding:4}} />
  );
}

// ── Photo député ──────────────────────────────────────────────────────────────
function PhotoDepute({url,prenom,nom,groupe,size=40}:{url:string;prenom:string;nom:string;groupe:string;size?:number}) {
  const [err,setErr]=useState(false);
  const col=c(groupe);
  const ini=`${prenom[0]??""}${nom[0]??""}`.toUpperCase();
  if(err) return (
    <div style={{width:size,height:size,borderRadius:"50%",background:`linear-gradient(135deg,${col}cc,${col})`,
      fontSize:size*0.32,flexShrink:0}} className="flex items-center justify-center text-white font-bold">
      {ini}
    </div>
  );
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={url} alt={`${prenom} ${nom}`} onError={()=>setErr(true)}
    style={{width:size,height:size,borderRadius:"50%",objectFit:"cover",objectPosition:"top",flexShrink:0}} />;
}

// ── Photo ministre ────────────────────────────────────────────────────────────
function PhotoMinistre({url,initiales,couleur,size=52,isTop=false}:{url:string;initiales:string;couleur:string;size?:number;isTop?:boolean}) {
  const [err,setErr]=useState(false);
  const s=isTop?size:size;
  if(err||!url) return (
    <div style={{width:s,height:s,borderRadius:"50%",background:`linear-gradient(135deg,${couleur}cc,${couleur})`,
      fontSize:s*0.35,flexShrink:0,border:`2px solid ${couleur}30`}}
      className="flex items-center justify-center text-white font-black">
      {initiales}
    </div>
  );
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={url} alt={initiales} onError={()=>setErr(true)}
    style={{width:s,height:s,borderRadius:"50%",objectFit:"cover",objectPosition:"top",
      flexShrink:0,border:`2px solid ${couleur}30`}} />;
}

// ── Hémicycle ─────────────────────────────────────────────────────────────────
function Hemicycle({partis}:{partis:Parti[]}) {
  const [hov,setHov]=useState<string|null>(null);
  const W=560,CX=280,CY=310;
  const RADII=[100,130,160,190];
  const SEATS=577;
  const sorted=[...partis].filter(p=>p.nb_sieges>0)
    .sort((a,b)=>(ORDRE_POLITIQUE.indexOf(a.id)??99)-(ORDRE_POLITIQUE.indexOf(b.id)??99));
  const dots:{x:number;y:number;color:string;groupe:string}[]=[];
  let placed=0;
  sorted.forEach(p=>{
    for(let s=0;s<p.nb_sieges;s++){
      const idx=placed+s,row=idx%RADII.length,r=RADII[row];
      const angle=Math.PI-(idx/SEATS)*Math.PI;
      dots.push({x:CX+r*Math.cos(angle),y:CY-r*Math.sin(angle),color:p.couleur,groupe:p.id});
    }
    placed+=p.nb_sieges;
  });
  const hovP=hov?partis.find(p=>p.id===hov):null;
  return (
    <svg viewBox={`0 0 ${W} ${CY+30}`} className="w-full" style={{maxHeight:330}}>
      {RADII.map(r=><path key={r} d={`M ${CX-r} ${CY} A ${r} ${r} 0 0 1 ${CX+r} ${CY}`}
        fill="none" stroke="currentColor" strokeOpacity={0.04} strokeWidth={1.5}/>)}
      {dots.map((d,i)=><circle key={i} cx={d.x} cy={d.y}
        r={hov===d.groupe?5.5:4} fill={d.color}
        opacity={hov&&hov!==d.groupe?0.15:0.92}
        style={{transition:"all .2s",cursor:"pointer"}}
        onMouseEnter={()=>setHov(d.groupe)} onMouseLeave={()=>setHov(null)}/>)}
      {!hovP&&<>
        <text x={CX} y={CY-22} textAnchor="middle" fontSize={30} fontWeight={800} fill="currentColor">{SEATS}</text>
        <text x={CX} y={CY-4} textAnchor="middle" fontSize={11} fill="currentColor" opacity={0.35}>sièges totaux</text>
      </>}
      {hovP&&<>
        <text x={CX} y={CY-22} textAnchor="middle" fontSize={22} fontWeight={800} fill={hovP.couleur}>{hovP.nb_sieges}</text>
        <text x={CX} y={CY-4} textAnchor="middle" fontSize={12} fill={hovP.couleur} fontWeight={600}>{hovP.nom_court}</text>
      </>}
    </svg>
  );
}

// ── Card parti ────────────────────────────────────────────────────────────────
function PartiCard({parti}:{parti:Parti}) {
  const col=parti.couleur;
  const pct=((parti.nb_sieges/577)*100).toFixed(1);
  return (
    <a href={`/partis/${parti.slug}`}
      className="group block relative overflow-hidden rounded-2xl border transition-all duration-300 hover:-translate-y-1 hover:shadow-xl"
      style={{background:"var(--surface)",borderColor:"var(--border)"}}>
      <div className="h-1 w-full" style={{background:col}}/>
      <div className="p-5">
        <div className="flex items-start justify-between mb-4">
          <LogoParti partiId={parti.id} nom={parti.nom} size={52}/>
          <div className="text-right">
            <p className="text-2xl font-black" style={{color:col}}>{parti.nb_sieges}</p>
            <p className="text-xs" style={{color:"var(--text-3)"}}>sièges</p>
          </div>
        </div>
        <h3 className="text-sm font-bold leading-tight mb-0.5" style={{color:"var(--text-1)"}}>{parti.nom}</h3>
        <p className="text-xs mb-4" style={{color:"var(--text-3)"}}>{parti.orientation}</p>
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs" style={{color:"var(--text-3)"}}>
            <span>Part hémicycle</span>
            <span className="font-semibold" style={{color:col}}>{pct}%</span>
          </div>
          <div className="h-2 rounded-full overflow-hidden" style={{background:"var(--surface-2)"}}>
            <div className="h-full rounded-full" style={{width:`${Math.min(parseFloat(pct)*2,100)}%`,background:col}}/>
          </div>
        </div>
        <div className="mt-4 flex items-center gap-1 text-xs font-semibold opacity-0 group-hover:opacity-100 transition-opacity" style={{color:col}}>
          Voir le groupe <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7"/></svg>
        </div>
      </div>
    </a>
  );
}

// ── Card ministre ─────────────────────────────────────────────────────────────
function MinistreCard({m}:{m:Ministre}) {
  const [showDesc,setShowDesc]=useState(false);
  const isTop=m.rang<=1;
  const col=m.couleur||c(m.parti);
  return (
    <div className="rounded-2xl border overflow-hidden transition-all hover:shadow-lg"
      style={{borderColor:"var(--border)",background:"var(--surface)"}}>
      {isTop&&<div className="h-0.5 w-full" style={{background:`linear-gradient(90deg,${col},transparent)`}}/>}
      <div className="p-4 flex gap-3">
        <PhotoMinistre url={m.photo_url} initiales={m.initiales} couleur={col} size={isTop?56:44} isTop={isTop}/>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-1">
            <div className="min-w-0">
              {isTop&&<span className="text-xs font-bold" style={{color:col}}>
                {m.rang===0?"★ Président de la République":"Premier ministre"}
              </span>}
              <p className="text-sm font-bold truncate" style={{color:"var(--text-1)"}}>{m.prenom} {m.nom}</p>
              <p className="text-xs leading-tight mt-0.5" style={{color:"var(--text-2)"}}>{m.role}</p>
            </div>
          </div>
          <div className="flex items-center justify-between mt-2">
            <span className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full"
              style={{background:col+"18",color:col}}>
              <span className="w-1.5 h-1.5 rounded-full" style={{background:col}}/>
              {m.parti}
            </span>
            {m.description&&(
              <button onClick={()=>setShowDesc(!showDesc)} className="text-xs underline" style={{color:"var(--text-3)"}}>
                {showDesc?"Moins":"Info"}
              </button>
            )}
          </div>
          {showDesc&&m.description&&(
            <p className="text-xs mt-2 leading-relaxed" style={{color:"var(--text-3)"}}>{m.description}</p>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function AnnuairePage() {
  const [deputes,setDeputes]=useState<Depute[]>([]);
  const [partis,setPartis]=useState<Parti[]>([]);
  const [ministres,setMinistres]=useState<Ministre[]>([]);
  const [loading,setLoading]=useState(true);
  const [recherche,setRecherche]=useState("");
  const [section,setSection]=useState<"partis"|"gouvernement">("partis");
  const searchRef=useRef<HTMLInputElement>(null);

  useEffect(()=>{
    Promise.all([
      fetch(`${API}/deputes?limit=700`).then(r=>r.json()),
      fetch(`${API}/partis`).then(r=>r.json()),
      fetch(`${API}/gouvernement`).then(r=>r.json()),
    ]).then(([dep,par,gov])=>{
      setDeputes(Array.isArray(dep)?dep:dep.items??[]);
      setPartis(Array.isArray(par)?par.filter((p:Parti)=>p.nb_sieges>0):[]);
      setMinistres(Array.isArray(gov)?gov:[]);
      setLoading(false);
    }).catch(()=>setLoading(false));
  },[]);

  const resultats=useMemo(()=>{
    if(recherche.trim().length<2)return[];
    const q=normalize(recherche);
    return deputes.filter(d=>normalize(`${d.prenom} ${d.nom}`).includes(q)).slice(0,10);
  },[deputes,recherche]);

  if(loading) return (
    <div className="min-h-screen flex items-center justify-center" style={{background:"var(--bg)"}}>
      <div className="flex flex-col items-center gap-4">
        <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"/>
        <p className="text-sm" style={{color:"var(--text-3)"}}>Chargement des données parlementaires…</p>
      </div>
    </div>
  );

  const president=ministres.find(m=>m.rang===0);
  const pm=ministres.find(m=>m.rang===1);
  const autresMinistres=ministres.filter(m=>m.rang>1);

  return (
    <div className="min-h-screen" style={{background:"var(--bg)"}}>

      {/* ── HERO ─────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden border-b" style={{borderColor:"var(--border)"}}>
        <div className="absolute inset-0 pointer-events-none" style={{
          backgroundImage:"linear-gradient(var(--border) 1px,transparent 1px),linear-gradient(90deg,var(--border) 1px,transparent 1px)",
          backgroundSize:"48px 48px",opacity:0.5}}/>
        <div className="relative max-w-7xl mx-auto px-6 py-12">
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-12 items-start">

            {/* Gauche */}
            <div className="lg:col-span-2 flex flex-col justify-center pt-4">
              <p className="text-xs font-bold tracking-[0.2em] text-blue-600 uppercase mb-3">XVIIe Législature · Avril 2026</p>
              <h1 className="text-4xl font-black tracking-tight mb-2" style={{color:"var(--text-1)"}}>Annuaire</h1>
              <p className="text-base mb-8" style={{color:"var(--text-2)"}}>
                {deputes.length} députés · {partis.length} groupes · {ministres.length} membres du gouvernement
              </p>

              {/* Recherche */}
              <div className="relative">
                <div className="flex items-center gap-3 px-4 py-3.5 rounded-2xl border-2 transition-all focus-within:border-blue-500 focus-within:shadow-lg"
                  style={{background:"var(--surface)",borderColor:"var(--border-2)"}}>
                  <svg className="w-5 h-5 flex-shrink-0" style={{color:"var(--text-3)"}} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z"/>
                  </svg>
                  <input ref={searchRef} type="search" placeholder="Rechercher un député par nom…"
                    value={recherche} onChange={e=>setRecherche(e.target.value)}
                    className="flex-1 bg-transparent outline-none text-sm font-medium placeholder:font-normal"
                    style={{color:"var(--text-1)"}}/>
                  {recherche&&<button onClick={()=>setRecherche("")} style={{color:"var(--text-3)"}}>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                  </button>}
                </div>
                {recherche.trim().length>=2&&(
                  <div className="absolute top-full left-0 right-0 mt-2 rounded-2xl border overflow-hidden z-30"
                    style={{background:"var(--surface)",borderColor:"var(--border)",boxShadow:"var(--shadow-lg)"}}>
                    {resultats.length>0?(
                      <div className="py-2">
                        <p className="text-xs font-semibold px-4 py-2" style={{color:"var(--text-3)"}}>{resultats.length} résultat{resultats.length>1?"s":""}</p>
                        {resultats.map(d=>(
                          <div key={d.id} className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors cursor-pointer">
                            <PhotoDepute url={d.photo_url} prenom={d.prenom} nom={d.nom} groupe={d.groupe} size={40}/>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-semibold truncate" style={{color:"var(--text-1)"}}>{d.prenom} <span className="font-bold">{d.nom}</span></p>
                              <p className="text-xs truncate" style={{color:"var(--text-3)"}}>{d.circonscription}</p>
                            </div>
                            <span className="text-xs font-bold px-2 py-1 rounded-lg flex-shrink-0" style={{background:c(d.groupe)+"18",color:c(d.groupe)}}>{d.groupe}</span>
                          </div>
                        ))}
                      </div>
                    ):(
                      <div className="py-10 text-center"><p className="text-sm" style={{color:"var(--text-3)"}}>Aucun résultat pour « {recherche} »</p></div>
                    )}
                  </div>
                )}
              </div>

              {/* Stats rapides */}
              <div className="grid grid-cols-3 gap-3 mt-6">
                {[{v:deputes.length,l:"Députés"},{v:577,l:"Sièges"},{v:ministres.length,l:"Ministres"}].map(s=>(
                  <div key={s.l} className="rounded-xl p-4 border" style={{background:"var(--surface)",borderColor:"var(--border)"}}>
                    <p className="text-2xl font-black" style={{color:"var(--text-1)"}}>{s.v}</p>
                    <p className="text-xs mt-0.5" style={{color:"var(--text-3)"}}>{s.l}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Hémicycle */}
            <div className="lg:col-span-3">
              <div className="rounded-3xl border p-6" style={{background:"var(--surface)",borderColor:"var(--border)"}}>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-bold" style={{color:"var(--text-1)"}}>Répartition des sièges</p>
                  <span className="text-xs px-2 py-1 rounded-full" style={{background:"var(--surface-2)",color:"var(--text-3)"}}>Survolez pour explorer</span>
                </div>
                <Hemicycle partis={partis}/>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-2 mt-5 pt-5 border-t" style={{borderColor:"var(--border)"}}>
                  {[...partis].sort((a,b)=>b.nb_sieges-a.nb_sieges).map(p=>(
                    <a key={p.id} href={`/partis/${p.slug}`} className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                      <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{background:p.couleur}}/>
                      <span className="text-xs truncate" style={{color:"var(--text-2)"}}>
                        <span className="font-semibold">{p.nom_court}</span>
                        <span style={{color:"var(--text-3)"}}> {p.nb_sieges}</span>
                      </span>
                    </a>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── NAVIGATION ───────────────────────────────────────────────────── */}
      <div className="sticky top-16 z-20 border-b" style={{background:"var(--surface)",borderColor:"var(--border)"}}>
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-1 h-12 items-center">
            {(["partis","gouvernement"] as const).map(s=>(
              <button key={s} onClick={()=>setSection(s)}
                className="px-5 py-2 text-sm font-semibold rounded-xl transition-all"
                style={{color:section===s?"var(--blue)":"var(--text-2)",background:section===s?"var(--blue-light)":"transparent"}}>
                {s==="partis"?`Groupes politiques (${partis.length})`:`Gouvernement Lecornu II (${ministres.length})`}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-10">

        {/* ── PARTIS ───────────────────────────────────────────────────────── */}
        {section==="partis"&&(
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {[...partis].sort((a,b)=>b.nb_sieges-a.nb_sieges).map((p,i)=>(
              <div key={p.id} style={{animationDelay:`${i*40}ms`}} className="animate-fade-up">
                <PartiCard parti={p}/>
              </div>
            ))}
          </div>
        )}

        {/* ── GOUVERNEMENT ─────────────────────────────────────────────────── */}
        {section==="gouvernement"&&(
          <section className="space-y-8">
            {/* Bandeau info */}
            <div className="rounded-2xl border p-4 flex items-start gap-3" style={{background:"var(--surface)",borderColor:"var(--border)"}}>
              <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" style={{background:"var(--blue-light)"}}>
                <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold" style={{color:"var(--text-1)"}}>Gouvernement Lecornu II — remanié le 26 février 2026</p>
                <p className="text-xs mt-0.5" style={{color:"var(--text-3)"}}>
                  Sébastien Lecornu est Premier ministre depuis le 9 septembre 2025. Remaniement suite au départ de Rachida Dati (municipales Paris) et Amélie de Montchalin (Cour des comptes).
                </p>
              </div>
            </div>

            {/* Président + PM */}
            <div>
              <p className="text-xs font-bold tracking-widest uppercase mb-4" style={{color:"var(--text-3)"}}>Exécutif</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[president,pm].filter(Boolean).map((m,i)=>m&&<MinistreCard key={i} m={m}/>)}
              </div>
            </div>

            {/* Ministres */}
            <div>
              <p className="text-xs font-bold tracking-widest uppercase mb-4" style={{color:"var(--text-3)"}}>Ministres</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {autresMinistres.map((m,i)=><MinistreCard key={i} m={m}/>)}
              </div>
            </div>

            {/* Composition par parti */}
            <div className="rounded-2xl border p-6" style={{background:"var(--surface)",borderColor:"var(--border)"}}>
              <h3 className="text-sm font-bold mb-5" style={{color:"var(--text-1)"}}>Composition par parti</h3>
              <div className="flex flex-wrap gap-3">
                {Object.entries(ministres.reduce<Record<string,number>>((acc,m)=>{acc[m.parti]=(acc[m.parti]??0)+1;return acc},{}))
                  .sort((a,b)=>b[1]-a[1])
                  .map(([parti,count])=>{
                    const col=c(parti);
                    return (
                      <div key={parti} className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold"
                        style={{background:col+"18",color:col}}>
                        <LogoParti partiId={parti} nom={parti} size={24}/>
                        <span>{parti}</span>
                        <span className="w-5 h-5 rounded-full flex items-center justify-center text-xs font-black text-white"
                          style={{background:col}}>{count}</span>
                      </div>
                    );
                  })}
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}