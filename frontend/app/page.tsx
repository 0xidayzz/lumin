"use client";

import { useState, useEffect, useRef } from "react";

const API = "http://localhost:8000";

interface StatsByGroupe { groupe:string;count:number;couleur:string; }
interface Stats { total_deputes:number;nb_groupes:number;by_groupe:StatsByGroupe[]; }
interface Parti { id:string;slug:string;nom:string;nom_court:string;couleur:string;nb_sieges:number; }

const ORDRE = ["LFI","GDR","ECO","SOC","NFP","LIOT","MODEM","ENS","REN","HOR","DR","LR","RN","NI"];
const COULEURS: Record<string,string> = {
  RN:"#003189",DR:"#0D47A1",LR:"#0D47A1",HOR:"#1565C0",ENS:"#FF6D00",REN:"#FF6D00",
  NFP:"#8B0000",MODEM:"#FF8F00",SOC:"#E91E63",ECO:"#2E7D32",LFI:"#B71C1C",
  GDR:"#C62828",LIOT:"#6A1B9A",NI:"#607D8B",
};

// ── Actualités réelles — avril 2026 ─────────────────────────────────────────
const ACTUS = [
  {
    tag:"Gouvernement", couleur:"#FF6D00",
    titre:"Lecornu remanié : Pégard à la Culture, Amiel aux Comptes publics",
    date:"26 fév. 2026",
    desc:"Suite au départ de Rachida Dati (candidate aux municipales à Paris) et d'Amélie de Montchalin (Cour des comptes), le gouvernement Lecornu II a été remanié. Catherine Pégard, ancienne présidente du château de Versailles, prend la Culture."
  },
  {
    tag:"Municipales 2026", couleur:"#1D4ED8",
    titre:"Élections municipales : campagne lancée dans toutes les communes",
    date:"Mars 2026",
    desc:"Lecornu juge que « les urnes n'ont sacré personne » et défend sa méthode du compromis face aux maires. Rachida Dati candidate à Paris, Gabriel Attal mobilisé sur le terrain."
  },
  {
    tag:"Budget 2026", couleur:"#0F766E",
    titre:"Le budget 2026 adopté après de longues négociations parlementaires",
    date:"Déc. 2025",
    desc:"Le gouvernement a réussi à faire adopter le budget 2026 grâce à l'abstention du PS (qui obtient la suspension de la réforme des retraites jusqu'en 2027) et de LIOT. Objectif : ramener le déficit à 5,4% du PIB."
  },
  {
    tag:"Justice", couleur:"#003189",
    titre:"Inéligibilité de Marine Le Pen : la cour d'appel confirme",
    date:"Mars 2025",
    desc:"La condamnation pour détournement de fonds européens et l'inéligibilité de 5 ans de Marine Le Pen ont été confirmées en appel. Jordan Bardella s'impose comme figure centrale du RN pour 2027."
  },
  {
    tag:"Politique", couleur:"#7C3AED",
    titre:"Édouard Philippe appelle Macron à démissionner",
    date:"Déc. 2025",
    desc:"Après le vote du budget, le président d'Horizons et candidat à la présidentielle 2027 a publiquement enjoint Emmanuel Macron à démissionner, fracturant la coalition présidentielle."
  },
  {
    tag:"Santé mentale", couleur:"#059669",
    titre:"Santé mentale : Grande cause nationale 2026",
    date:"Jan. 2026",
    desc:"Le gouvernement a fait de la santé mentale la grande cause nationale de 2026. Des mesures ambitieuses sont annoncées pour renforcer la prise en charge psychiatrique et lutter contre la souffrance psychologique."
  },
];

// ── Compteur animé ────────────────────────────────────────────────────────────
function Counter({target,duration=1200}:{target:number;duration?:number}) {
  const [val,setVal]=useState(0);
  const raf=useRef<number>(0);
  useEffect(()=>{
    const start=performance.now();
    const animate=(now:number)=>{
      const p=Math.min((now-start)/duration,1);
      const e=1-Math.pow(1-p,3);
      setVal(Math.round(e*target));
      if(p<1)raf.current=requestAnimationFrame(animate);
    };
    raf.current=requestAnimationFrame(animate);
    return ()=>cancelAnimationFrame(raf.current);
  },[target,duration]);
  return <>{val.toLocaleString("fr")}</>;
}

// ── Mini hémicycle ────────────────────────────────────────────────────────────
function MiniHemicycle({groupes}:{groupes:StatsByGroupe[]}) {
  const W=340,CX=170,CY=200;
  const RADII=[80,104,128];
  const SEATS=577;
  const sorted=[...groupes].sort((a,b)=>(ORDRE.indexOf(a.groupe)??99)-(ORDRE.indexOf(b.groupe)??99));
  const dots:{x:number;y:number;color:string}[]=[];
  let placed=0;
  sorted.forEach(g=>{
    for(let s=0;s<g.count;s++){
      const idx=placed+s,row=idx%RADII.length,r=RADII[row];
      const angle=Math.PI-(idx/SEATS)*Math.PI;
      dots.push({x:CX+r*Math.cos(angle),y:CY-r*Math.sin(angle),color:g.couleur});
    }
    placed+=g.count;
  });
  return (
    <svg viewBox={`0 0 ${W} ${CY+20}`} className="w-full">
      {RADII.map(r=><path key={r} d={`M ${CX-r} ${CY} A ${r} ${r} 0 0 1 ${CX+r} ${CY}`}
        fill="none" stroke="currentColor" strokeOpacity={0.05} strokeWidth={1}/>)}
      {dots.map((d,i)=><circle key={i} cx={d.x} cy={d.y} r={4.2} fill={d.color} opacity={0.88}/>)}
      <text x={CX} y={CY-14} textAnchor="middle" fontSize={22} fontWeight={700} fill="currentColor">{SEATS}</text>
      <text x={CX} y={CY+2} textAnchor="middle" fontSize={10} fill="currentColor" opacity={0.4}>sièges</text>
    </svg>
  );
}

// ── Logo parti (proxy) ────────────────────────────────────────────────────────
function LogoMini({partiId,nom,size=40}:{partiId:string;nom:string;size?:number}) {
  const [err,setErr]=useState(false);
  const col=COULEURS[partiId]??"#888";
  if(err) return (
    <div style={{width:size,height:size,background:col,borderRadius:8,fontSize:size*0.28}}
      className="flex items-center justify-center text-white font-black">{partiId.slice(0,3)}</div>
  );
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={`${API}/proxy/logo/${partiId}`} alt={nom} onError={()=>setErr(true)}
    style={{width:size,height:size,objectFit:"contain",background:"#fff",borderRadius:8,padding:2}}/>;
}

export default function HomePage() {
  const [stats,setStats]=useState<Stats|null>(null);
  const [partis,setPartis]=useState<Parti[]>([]);

  useEffect(()=>{
    fetch(`${API}/stats`).then(r=>r.json()).then(setStats).catch(()=>{});
    fetch(`${API}/partis`).then(r=>r.json()).then(setPartis).catch(()=>{});
  },[]);

  const maxCount=stats?Math.max(...stats.by_groupe.map(g=>g.count)):1;
  const topPartis=partis.filter(p=>p.nb_sieges>0).slice(0,6);

  return (
    <div className="min-h-screen">

      {/* ── HERO ──────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden grid-bg border-b" style={{borderColor:"var(--border)"}}>
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/8 rounded-full blur-3xl pointer-events-none"/>
        <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-cyan-500/6 rounded-full blur-3xl pointer-events-none"/>

        <div className="relative max-w-7xl mx-auto px-6 py-20 lg:py-28">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">

            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium mb-6 animate-fade-up"
                style={{borderColor:"var(--border-2)",background:"var(--surface)",color:"var(--text-2)"}}>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse-dot"/>
                XVIIe législature · Gouvernement Lecornu II · Avril 2026
              </div>

              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.05] mb-6 animate-fade-up delay-100">
                La politique,<br/>
                <span className="text-gradient">décodée.</span>
              </h1>

              <p className="text-lg leading-relaxed mb-10 max-w-lg animate-fade-up delay-200" style={{color:"var(--text-2)"}}>
                Lumin analyse chaque débat, chaque vote, chaque loi de l'Assemblée Nationale et vous les explique sans jargon.
              </p>

              <div className="flex flex-wrap gap-3 animate-fade-up delay-300">
                <a href="/annuaire" className="px-6 py-3 rounded-xl text-white text-sm font-semibold hover:opacity-90 transition-opacity shadow-md"
                  style={{background:"var(--blue)"}}>Explorer l'annuaire</a>
                <a href="/lois" className="px-6 py-3 rounded-xl border text-sm font-semibold transition-colors hover:bg-[var(--surface-2)]"
                  style={{borderColor:"var(--border-2)",color:"var(--text-1)"}}>Voir les lois →</a>
              </div>

              {stats&&(
                <div className="grid grid-cols-3 gap-4 mt-12 animate-fade-up delay-400">
                  {[{l:"Députés",v:stats.total_deputes},{l:"Groupes",v:stats.nb_groupes},{l:"Sièges",v:577}].map(s=>(
                    <div key={s.l} className="card p-4">
                      <p className="text-2xl font-bold" style={{color:"var(--text-1)"}}><Counter target={s.v}/></p>
                      <p className="text-xs mt-0.5" style={{color:"var(--text-3)"}}>{s.l}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="animate-fade-up delay-200">
              <div className="card-lg p-6 glow-blue">
                <div className="flex items-center justify-between mb-4">
                  <p className="text-sm font-semibold" style={{color:"var(--text-1)"}}>Composition de l'hémicycle</p>
                  <a href="/annuaire" className="text-xs hover:underline" style={{color:"var(--blue)"}}>Voir tout →</a>
                </div>
                {stats?<MiniHemicycle groupes={stats.by_groupe}/>:
                  <div className="h-48 rounded-xl animate-pulse" style={{background:"var(--surface-2)"}}/>}
                {stats&&(
                  <div className="mt-5 space-y-2.5">
                    {stats.by_groupe.slice(0,6).map(g=>{
                      const col=COULEURS[g.groupe]??g.couleur??"#888";
                      const pct=(g.count/maxCount)*100;
                      return (
                        <a key={g.groupe} href={`/partis/${g.groupe.toLowerCase()}`}
                          className="flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer">
                          <div className="w-3 h-3 rounded-full flex-shrink-0" style={{background:col}}/>
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between text-xs mb-1">
                              <span className="font-medium truncate" style={{color:"var(--text-1)"}}>{g.groupe}</span>
                              <span style={{color:"var(--text-3)"}}>{g.count}</span>
                            </div>
                            <div className="w-full rounded-full h-1.5" style={{background:"var(--surface-2)"}}>
                              <div className="h-1.5 rounded-full" style={{width:`${pct}%`,background:col}}/>
                            </div>
                          </div>
                        </a>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── ACTUALITÉS ──────────────────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="flex items-end justify-between mb-8">
          <div>
            <p className="text-xs font-semibold tracking-widest text-blue-600 uppercase mb-1">Actualité</p>
            <h2 className="text-2xl font-bold" style={{color:"var(--text-1)"}}>Ce qui s'est passé à l'Assemblée</h2>
          </div>
          <span className="text-xs hidden sm:block" style={{color:"var(--text-3)"}}>Données au 10 avril 2026</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {ACTUS.map((a,i)=>(
            <article key={i} className="card p-5 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 animate-fade-up cursor-pointer"
              style={{animationDelay:`${i*60}ms`}}>
              <div className="flex items-center justify-between mb-3">
                <span className="badge text-xs font-semibold" style={{background:a.couleur+"18",color:a.couleur}}>{a.tag}</span>
                <span className="text-xs" style={{color:"var(--text-3)"}}>{a.date}</span>
              </div>
              <h3 className="text-sm font-semibold mb-2 leading-snug" style={{color:"var(--text-1)"}}>{a.titre}</h3>
              <p className="text-xs leading-relaxed line-clamp-2" style={{color:"var(--text-2)"}}>{a.desc}</p>
            </article>
          ))}
        </div>
      </section>

      {/* ── PARTIS ──────────────────────────────────────────────────────────── */}
      <section className="border-y" style={{background:"var(--surface)",borderColor:"var(--border)"}}>
        <div className="max-w-7xl mx-auto px-6 py-16">
          <div className="flex items-end justify-between mb-8">
            <div>
              <p className="text-xs font-semibold tracking-widest text-blue-600 uppercase mb-1">Politique</p>
              <h2 className="text-2xl font-bold" style={{color:"var(--text-1)"}}>Les forces en présence</h2>
            </div>
            <a href="/annuaire" className="text-sm font-medium hover:underline" style={{color:"var(--blue)"}}>Annuaire complet →</a>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {topPartis.map((p,i)=>(
              <a key={p.id} href={`/partis/${p.slug}`}
                className="card p-4 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 text-center group animate-fade-up"
                style={{animationDelay:`${i*50}ms`}}>
                <div className="mx-auto mb-3 group-hover:scale-110 transition-transform">
                  <LogoMini partiId={p.id} nom={p.nom_court} size={44}/>
                </div>
                <p className="text-lg font-bold" style={{color:"var(--text-1)"}}>{p.nb_sieges}</p>
                <p className="text-xs mt-0.5" style={{color:"var(--text-3)"}}>sièges</p>
                <p className="text-xs font-medium mt-1 truncate" style={{color:"var(--text-2)"}}>{p.nom_court}</p>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* ── FONCTIONNALITÉS ─────────────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <p className="text-xs font-semibold tracking-widest text-blue-600 uppercase mb-2">Lumin</p>
          <h2 className="text-3xl font-bold" style={{color:"var(--text-1)"}}>Comprendre la démocratie, simplement</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {icon:"⚖️",titre:"Lois en langage clair",desc:"Chaque texte de loi est réécrit par une IA locale (Mistral/Ollama) pour que vous compreniez ce qui change concrètement dans votre vie, sans jargon juridique.",couleur:"#1d4ed8"},
            {icon:"👥",titre:"Suivez vos représentants",desc:"618 profils complets : interventions, votes, cohérence avec leur parti, présence en séance — tout ce qu'un citoyen doit savoir sur ses élus.",couleur:"#0891b2"},
            {icon:"📊",titre:"Votes & scrutins",desc:"Pour chaque loi, visualisez comment chaque groupe et chaque député a voté, avec des graphiques comparatifs clairs et accessibles.",couleur:"#7c3aed"},
          ].map((f,i)=>(
            <div key={i} className="card p-6 animate-fade-up" style={{animationDelay:`${i*80}ms`}}>
              <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl mb-4" style={{background:f.couleur+"18"}}>{f.icon}</div>
              <h3 className="text-base font-semibold mb-2" style={{color:"var(--text-1)"}}>{f.titre}</h3>
              <p className="text-sm leading-relaxed" style={{color:"var(--text-2)"}}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── FOOTER ──────────────────────────────────────────────────────────── */}
      <footer className="border-t" style={{borderColor:"var(--border)",background:"var(--surface)"}}>
        <div className="max-w-7xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{background:"var(--blue)"}}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <span className="font-bold text-sm" style={{color:"var(--text-1)"}}>Lumin</span>
            <span className="text-xs" style={{color:"var(--text-3)"}}>— Open source</span>
          </div>
          <p className="text-xs" style={{color:"var(--text-3)"}}>
            Données : Assemblée Nationale · nosdeputes.fr · Légifrance · Gouvernement Lecornu II (26 fév. 2026)
          </p>
        </div>
      </footer>
    </div>
  );
}