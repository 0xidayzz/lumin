"use client";

import { useState, useEffect, useRef } from "react";

const API = "http://localhost:8000";

// ── Types ─────────────────────────────────────────────────────────────────────
interface StatsByGroupe { groupe: string; count: number; couleur: string; }
interface Stats { total_deputes: number; nb_groupes: number; by_groupe: StatsByGroupe[]; }
interface Parti { id: string; slug: string; nom: string; nom_court: string; couleur: string; nb_sieges: number; orientation: string; }

// ── Actualités statiques (en attendant le pipeline) ────────────────────────
const ACTUS = [
  { tag: "Gouvernement", couleur: "#FF6D00", titre: "François Bayrou nommé Premier ministre", date: "13 jan. 2025", desc: "Le fondateur du MoDem forme son gouvernement après la chute de Michel Barnier sur une motion de censure historique." },
  { tag: "Justice",      couleur: "#003189", titre: "Marine Le Pen condamnée — inéligibilité confirmée", date: "31 mars 2025", desc: "La cour d'appel confirme la condamnation pour détournement de fonds européens et l'inéligibilité de 5 ans." },
  { tag: "Budget",       couleur: "#E91E63", titre: "Déficit public : la France vise 5,4% du PIB en 2025", date: "Avr. 2025", desc: "Le gouvernement Bayrou présente un budget de rigueur face à la pression des marchés financiers." },
  { tag: "Parlement",    couleur: "#2E7D32", titre: "Motion de censure NFP rejetée d'extrême justesse", date: "Fév. 2025", desc: "Le gouvernement Bayrou survit à la motion de censure déposée par le Nouveau Front Populaire, LIOT s'étant abstenu." },
  { tag: "Réformes",     couleur: "#1565C0", titre: "Réforme des retraites : Bayrou ouvre une concertation", date: "Mars 2025", desc: "Le Premier ministre propose une table ronde avec les syndicats sur l'âge de départ, sans s'engager sur une abrogation." },
  { tag: "International","couleur": "#0D47A1", titre: "Ukraine : la France maintient son soutien militaire", date: "Avr. 2025", desc: "Le ministre Lecornu annonce une enveloppe supplémentaire de 2 milliards d'euros d'aide militaire à Kiev." },
];

// ── Ordre politique hémicycle ─────────────────────────────────────────────
const ORDRE = ["LFI","GDR","ECO","SOC","NFP","LIOT","MODEM","ENS","HOR","LR","RN","NI"];
const COULEURS: Record<string,string> = {
  RN:"#003189",LR:"#0D47A1",HOR:"#1565C0",ENS:"#FF6D00",
  MODEM:"#FF8F00",SOC:"#E91E63",ECO:"#2E7D32",LFI:"#B71C1C",
  GDR:"#C62828",LIOT:"#6A1B9A",NFP:"#8B0000",NI:"#607D8B",
};

// ── Compteur animé ────────────────────────────────────────────────────────
function Counter({ target, duration = 1200 }: { target: number; duration?: number }) {
  const [val, setVal] = useState(0);
  const raf = useRef<number>(0);
  useEffect(() => {
    const start = performance.now();
    const animate = (now: number) => {
      const p = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setVal(Math.round(eased * target));
      if (p < 1) raf.current = requestAnimationFrame(animate);
    };
    raf.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf.current);
  }, [target, duration]);
  return <>{val.toLocaleString("fr")}</>;
}

// ── Mini hémicycle SVG ────────────────────────────────────────────────────
function MiniHemicycle({ groupes }: { groupes: StatsByGroupe[] }) {
  const W = 340, CX = 170, CY = 200;
  const RADII = [80, 104, 128];
  const SEATS = 577;

  const sorted = [...groupes].sort(
    (a, b) => (ORDRE.indexOf(a.groupe) ?? 99) - (ORDRE.indexOf(b.groupe) ?? 99)
  );

  const dots: { x: number; y: number; color: string }[] = [];
  let placed = 0;

  sorted.forEach((g) => {
    for (let s = 0; s < g.count; s++) {
      const idx = placed + s;
      const row = idx % RADII.length;
      const r = RADII[row];
      const angle = Math.PI - (idx / SEATS) * Math.PI;
      dots.push({ x: CX + r * Math.cos(angle), y: CY - r * Math.sin(angle), color: g.couleur });
    }
    placed += g.count;
  });

  return (
    <svg viewBox={`0 0 ${W} ${CY + 20}`} className="w-full">
      {RADII.map((r) => (
        <path key={r} d={`M ${CX - r} ${CY} A ${r} ${r} 0 0 1 ${CX + r} ${CY}`}
          fill="none" stroke="currentColor" strokeOpacity={0.05} strokeWidth={1} />
      ))}
      {dots.map((d, i) => <circle key={i} cx={d.x} cy={d.y} r={4.2} fill={d.color} opacity={0.88} />)}
      <text x={CX} y={CY - 14} textAnchor="middle" fontSize={22} fontWeight={700} fill="currentColor">{SEATS}</text>
      <text x={CX} y={CY + 2}  textAnchor="middle" fontSize={10} fill="currentColor" opacity={0.4}>sièges</text>
    </svg>
  );
}

// ── Card actu ─────────────────────────────────────────────────────────────
function ActuCard({ a, delay }: { a: typeof ACTUS[0]; delay: number }) {
  return (
    <article
      className="card p-5 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 animate-fade-up cursor-pointer"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-center justify-between mb-3">
        <span
          className="badge text-xs font-semibold"
          style={{ background: a.couleur + "18", color: a.couleur }}
        >
          {a.tag}
        </span>
        <span className="text-xs text-[var(--text-3)]">{a.date}</span>
      </div>
      <h3 className="text-sm font-semibold text-[var(--text-1)] mb-2 leading-snug">{a.titre}</h3>
      <p className="text-xs text-[var(--text-2)] leading-relaxed line-clamp-2">{a.desc}</p>
    </article>
  );
}

// ── Barre de groupe ───────────────────────────────────────────────────────
function GroupeBar({ g, max }: { g: StatsByGroupe; max: number }) {
  const pct = (g.count / max) * 100;
  const color = COULEURS[g.groupe] ?? g.couleur ?? "#888";
  return (
    <div className="flex items-center gap-3 group cursor-pointer" onClick={() => window.location.href = `/partis/${g.groupe.toLowerCase()}`}>
      <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: color }} />
      <div className="flex-1 min-w-0">
        <div className="flex justify-between text-xs mb-1">
          <span className="font-medium text-[var(--text-1)] truncate">{g.groupe}</span>
          <span className="text-[var(--text-3)] ml-2">{g.count}</span>
        </div>
        <div className="w-full bg-[var(--surface-2)] rounded-full h-1.5">
          <div className="h-1.5 rounded-full" style={{ width: `${pct}%`, background: color }} />
        </div>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────
export default function HomePage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [partis, setPartis] = useState<Parti[]>([]);

  useEffect(() => {
    fetch(`${API}/stats`).then(r => r.json()).then(setStats).catch(() => {});
    fetch(`${API}/partis`).then(r => r.json()).then(setPartis).catch(() => {});
  }, []);

  const maxCount = stats ? Math.max(...stats.by_groupe.map(g => g.count)) : 1;
  const topPartis = partis.filter(p => p.nb_sieges > 0).slice(0, 6);

  return (
    <div className="min-h-screen">

      {/* ── HERO ─────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden grid-bg border-b border-[var(--border)]">
        {/* Glow décoratif */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/8 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-cyan-500/6 rounded-full blur-3xl pointer-events-none" />

        <div className="relative max-w-7xl mx-auto px-6 py-20 lg:py-28">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">

            {/* Texte */}
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-[var(--border-2)] bg-[var(--surface)] text-xs font-medium text-[var(--text-2)] mb-6 animate-fade-up">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse-dot" />
                XVIIe législature · Analyse par IA locale
              </div>

              <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.05] mb-6 animate-fade-up delay-100">
                La politique,<br />
                <span className="text-gradient">décodée.</span>
              </h1>

              <p className="text-lg text-[var(--text-2)] leading-relaxed mb-10 max-w-lg animate-fade-up delay-200">
                Lumin analyse chaque débat, chaque vote, chaque loi de l'Assemblée Nationale
                — et vous les explique sans jargon.
              </p>

              <div className="flex flex-wrap gap-3 animate-fade-up delay-300">
                <a href="/annuaire"
                  className="px-6 py-3 rounded-xl bg-[var(--blue)] text-white text-sm font-semibold hover:bg-blue-700 transition-colors shadow-md"
                >
                  Explorer l'annuaire
                </a>
                <a href="/lois"
                  className="px-6 py-3 rounded-xl border border-[var(--border-2)] bg-[var(--surface)] text-sm font-semibold text-[var(--text-1)] hover:bg-[var(--surface-2)] transition-colors"
                >
                  Voir les lois →
                </a>
              </div>

              {/* Stats hero */}
              {stats && (
                <div className="grid grid-cols-3 gap-4 mt-12 animate-fade-up delay-400">
                  {[
                    { label: "Députés", value: stats.total_deputes },
                    { label: "Groupes",  value: stats.nb_groupes },
                    { label: "Sièges",  value: 577 },
                  ].map((s) => (
                    <div key={s.label} className="card p-4">
                      <p className="text-2xl font-bold text-[var(--text-1)]">
                        <Counter target={s.value} />
                      </p>
                      <p className="text-xs text-[var(--text-3)] mt-0.5">{s.label}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Hémicycle + composition */}
            <div className="animate-fade-up delay-200">
              <div className="card-lg p-6 glow-blue">
                <div className="flex items-center justify-between mb-4">
                  <p className="text-sm font-semibold text-[var(--text-1)]">Composition de l'hémicycle</p>
                  <a href="/annuaire" className="text-xs text-[var(--blue)] hover:underline">Voir tout →</a>
                </div>

                {stats ? (
                  <MiniHemicycle groupes={stats.by_groupe} />
                ) : (
                  <div className="h-48 bg-[var(--surface-2)] rounded-xl animate-pulse" />
                )}

                {/* Barres des groupes */}
                {stats && (
                  <div className="mt-5 space-y-2.5">
                    {stats.by_groupe.slice(0, 6).map((g) => (
                      <GroupeBar key={g.groupe} g={g} max={maxCount} />
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── ACTUALITÉS ───────────────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="flex items-end justify-between mb-8">
          <div>
            <p className="text-xs font-semibold tracking-widest text-[var(--blue)] uppercase mb-1">Actualité</p>
            <h2 className="text-2xl font-bold text-[var(--text-1)]">Ce qui se passe à l'Assemblée</h2>
          </div>
          <span className="text-xs text-[var(--text-3)] hidden sm:block">Mis à jour quotidiennement</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {ACTUS.map((a, i) => <ActuCard key={i} a={a} delay={i * 60} />)}
        </div>
      </section>

      {/* ── PARTIS ───────────────────────────────────────────────────────── */}
      <section className="bg-[var(--surface)] border-y border-[var(--border)]">
        <div className="max-w-7xl mx-auto px-6 py-16">
          <div className="flex items-end justify-between mb-8">
            <div>
              <p className="text-xs font-semibold tracking-widest text-[var(--blue)] uppercase mb-1">Politique</p>
              <h2 className="text-2xl font-bold text-[var(--text-1)]">Les forces en présence</h2>
            </div>
            <a href="/annuaire" className="text-sm font-medium text-[var(--blue)] hover:underline">
              Voir l'annuaire complet →
            </a>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {topPartis.map((p, i) => (
              <a
                key={p.id}
                href={`/partis/${p.slug}`}
                className="card p-4 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 text-center group animate-fade-up"
                style={{ animationDelay: `${i * 50}ms` }}
              >
                <div
                  className="w-12 h-12 rounded-xl mx-auto flex items-center justify-center text-white font-bold text-xs mb-3 group-hover:scale-110 transition-transform shadow"
                  style={{ background: p.couleur }}
                >
                  {p.nom_court}
                </div>
                <p className="text-lg font-bold text-[var(--text-1)]">{p.nb_sieges}</p>
                <p className="text-xs text-[var(--text-3)] mt-0.5">sièges</p>
                <p className="text-xs font-medium text-[var(--text-2)] mt-1 truncate">{p.nom_court === p.nom ? p.nom : p.nom_court}</p>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* ── FONCTIONNALITÉS ──────────────────────────────────────────────── */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <p className="text-xs font-semibold tracking-widest text-[var(--blue)] uppercase mb-2">Lumin</p>
          <h2 className="text-3xl font-bold text-[var(--text-1)]">Comprendre la démocratie, simplement</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              icon: "⚖️",
              titre: "Lois en langage clair",
              desc: "Chaque texte de loi est réécrit par une IA locale (Mistral) pour que vous compreniez ce qui change concrètement dans votre vie.",
              couleur: "#1d4ed8",
            },
            {
              icon: "👥",
              titre: "Suivez vos représentants",
              desc: "618 profils complets : interventions, votes, cohérence avec leur parti, présence en séance — tout ce qu'un citoyen doit savoir.",
              couleur: "#0891b2",
            },
            {
              icon: "📊",
              titre: "Votes & scrutins",
              desc: "Pour chaque loi, visualisez comment chaque parti et chaque député a voté, avec des graphiques clairs et comparatifs.",
              couleur: "#7c3aed",
            },
          ].map((f, i) => (
            <div
              key={i}
              className="card p-6 animate-fade-up"
              style={{ animationDelay: `${i * 80}ms` }}
            >
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center text-xl mb-4"
                style={{ background: f.couleur + "18" }}
              >
                {f.icon}
              </div>
              <h3 className="text-base font-semibold text-[var(--text-1)] mb-2">{f.titre}</h3>
              <p className="text-sm text-[var(--text-2)] leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── FOOTER ──────────────────────────────────────────────────────── */}
      <footer className="border-t border-[var(--border)] bg-[var(--surface)]">
        <div className="max-w-7xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-[var(--blue)] rounded-lg flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <span className="font-bold text-sm text-[var(--text-1)]">Lumin</span>
            <span className="text-xs text-[var(--text-3)]">— Open source</span>
          </div>
          <p className="text-xs text-[var(--text-3)]">
            Données : Assemblée Nationale · nosdeputes.fr · Légifrance · Analyse IA locale
          </p>
        </div>
      </footer>

    </div>
  );
}