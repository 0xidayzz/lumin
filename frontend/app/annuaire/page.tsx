"use client";

import { useState, useEffect, useMemo, useRef } from "react";

const API = "http://localhost:8000";

// ── Types ────────────────────────────────────────────────────────────────────
interface Depute {
  id: string;
  prenom: string;
  nom: string;
  groupe: string;
  circonscription: string;
  photo_url: string;
}
interface Parti {
  id: string;
  slug: string;
  nom: string;
  nom_court: string;
  couleur: string;
  description: string;
  nb_sieges: number;
  orientation: string;
}
interface Ministre {
  nom: string;
  prenom: string;
  role: string;
  parti: string;
  rang: number;
}

// ── Config partis ─────────────────────────────────────────────────────────────
const COULEURS: Record<string, string> = {
  RN: "#003189", LR: "#0D47A1", HOR: "#1565C0", REN: "#FF6D00",
  MODEM: "#FF8F00", SOC: "#E91E63", ECO: "#2E7D32",
  LFI: "#B71C1C", GDR: "#C62828", LIOT: "#6A1B9A", NI: "#607D8B",
};
const LABELS: Record<string, string> = {
  RN: "Rassemblement National", LR: "Les Républicains", HOR: "Horizons",
  REN: "Renaissance", MODEM: "MoDem", SOC: "Socialistes",
  ECO: "Écologistes", LFI: "La France Insoumise", GDR: "GDR",
  LIOT: "LIOT", NI: "Non-Inscrits",
};

// Ordre politique gauche→droite pour l'hémicycle
const ORDRE_POLITIQUE = ["LFI", "GDR", "ECO", "SOC", "LIOT", "REN", "MODEM", "HOR", "LR", "RN", "NI"];

// ── Hémicycle SVG ─────────────────────────────────────────────────────────────
function Hemicycle({ partis, total }: { partis: Parti[]; total: number }) {
  const W = 500, H = 280, CX = 250, CY = 270;
  const ROWS = 3;
  const RADII = [120, 155, 190];
  const DOT = 5.5;
  const SEATS_TOTAL = 577;

  // Trie par ordre politique
  const sorted = [...partis].sort(
    (a, b) =>
      (ORDRE_POLITIQUE.indexOf(a.id) ?? 99) - (ORDRE_POLITIQUE.indexOf(b.id) ?? 99)
  );

  // Génère les points sur les arcs
  const allDots: { x: number; y: number; color: string; groupe: string }[] = [];
  let totalPlaced = 0;

  sorted.forEach((parti) => {
    const seats = parti.nb_sieges;
    if (!seats) return;
    // Répartit les sièges sur 3 rangées proportionnellement
    for (let s = 0; s < seats; s++) {
      const globalIdx = totalPlaced + s;
      const row = globalIdx % ROWS;
      const r = RADII[row];
      // Angle de 0° (gauche) à 180° (droite) sur le demi-cercle supérieur
      const fraction = globalIdx / SEATS_TOTAL;
      const angle = Math.PI - fraction * Math.PI; // de π à 0
      allDots.push({
        x: CX + r * Math.cos(angle),
        y: CY - r * Math.sin(angle),
        color: COULEURS[parti.id] ?? "#90A4AE",
        groupe: parti.id,
      });
    }
    totalPlaced += seats;
  });

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-xl mx-auto">
      {/* Arc de fond */}
      {RADII.map((r) => (
        <path
          key={r}
          d={`M ${CX - r} ${CY} A ${r} ${r} 0 0 1 ${CX + r} ${CY}`}
          fill="none"
          stroke="currentColor"
          strokeOpacity={0.06}
          strokeWidth={1}
        />
      ))}
      {/* Points */}
      {allDots.map((d, i) => (
        <circle key={i} cx={d.x} cy={d.y} r={DOT} fill={d.color} opacity={0.9} />
      ))}
      {/* Label centre */}
      <text x={CX} y={CY - 16} textAnchor="middle" fontSize={28} fontWeight={700} fill="currentColor">
        {SEATS_TOTAL}
      </text>
      <text x={CX} y={CY + 2} textAnchor="middle" fontSize={11} fill="currentColor" opacity={0.5}>
        sièges
      </text>
    </svg>
  );
}

// ── Composant photo ───────────────────────────────────────────────────────────
function Photo({ url, prenom, nom, groupe, size = "md" }: {
  url: string; prenom: string; nom: string; groupe: string; size?: "sm" | "md" | "lg";
}) {
  const [err, setErr] = useState(false);
  const initiales = `${prenom[0] ?? ""}${nom[0] ?? ""}`.toUpperCase();
  const color = COULEURS[groupe] ?? "#607D8B";
  const sz = size === "sm" ? "h-10 w-10 text-sm" : size === "lg" ? "h-20 w-20 text-xl" : "h-14 w-14 text-base";

  if (err) {
    return (
      <div
        className={`${sz} rounded-full flex items-center justify-center font-semibold text-white flex-shrink-0`}
        style={{ background: color }}
      >
        {initiales}
      </div>
    );
  }
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={url}
      alt={`${prenom} ${nom}`}
      onError={() => setErr(true)}
      className={`${sz} rounded-full object-cover object-top flex-shrink-0`}
      style={{ border: `2px solid ${color}30` }}
    />
  );
}

// ── Card député (recherche) ───────────────────────────────────────────────────
function DeputeCard({ d }: { d: Depute }) {
  const color = COULEURS[d.groupe] ?? "#607D8B";
  return (
    <div className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors cursor-pointer group">
      <Photo url={d.photo_url} prenom={d.prenom} nom={d.nom} groupe={d.groupe} size="sm" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
          {d.prenom} {d.nom}
        </p>
        <p className="text-xs text-slate-400 truncate">{d.circonscription}</p>
      </div>
      <span
        className="text-xs font-semibold px-2 py-0.5 rounded-full flex-shrink-0"
        style={{ background: color + "20", color }}
      >
        {d.groupe}
      </span>
    </div>
  );
}

// ── Card parti ────────────────────────────────────────────────────────────────
function PartiCard({ parti, onClick }: { parti: Parti; onClick: () => void }) {
  const color = parti.couleur;
  const total = 577;
  const pct = Math.round((parti.nb_sieges / total) * 100);

  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-100 dark:border-slate-700/50 p-5 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 group"
    >
      {/* En-tête */}
      <div className="flex items-start justify-between mb-4">
        <div
          className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-sm"
          style={{ background: color }}
        >
          {parti.nom_court}
        </div>
        <span className="text-2xl font-bold text-slate-900 dark:text-white">
          {parti.nb_sieges}
          <span className="text-sm font-normal text-slate-400 ml-1">sièges</span>
        </span>
      </div>

      {/* Nom */}
      <p className="text-sm font-semibold text-slate-900 dark:text-white mb-1 leading-tight">
        {parti.nom}
      </p>
      <p className="text-xs text-slate-400 mb-4">{parti.orientation}</p>

      {/* Barre de progression */}
      <div className="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-1.5">
        <div
          className="h-1.5 rounded-full transition-all"
          style={{ width: `${Math.min(pct * 2.5, 100)}%`, background: color }}
        />
      </div>
      <p className="text-xs text-slate-400 mt-1">{pct}% de l'hémicycle</p>

      {/* Hover arrow */}
      <div className="mt-4 flex items-center gap-1 text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity" style={{ color }}>
        Voir le parti
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </button>
  );
}

// ── Card gouvernement ─────────────────────────────────────────────────────────
function GouvernementSection({ ministres }: { ministres: Ministre[] }) {
  return (
    <section>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
          <svg className="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 21h18M3 10h18M3 7l9-4 9 4M4 10h1v11H4zm15 0h1v11h-1zm-7 0h2v11h-2z" />
          </svg>
        </div>
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Gouvernement</h2>
        <span className="text-sm text-slate-400">{ministres.length} membres</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {ministres.map((m, i) => {
          const color = COULEURS[m.parti] ?? "#607D8B";
          const initiales = (m.prenom[0] ?? "") + (m.nom[0] ?? "");
          return (
            <div
              key={i}
              className="flex items-center gap-3 p-3.5 bg-white dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-700/50"
            >
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold text-sm flex-shrink-0"
                style={{ background: color }}
              >
                {initiales || m.nom[0]}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                  {m.prenom} {m.nom}
                </p>
                <p className="text-xs text-slate-400 truncate">{m.role}</p>
                <span
                  className="text-xs font-medium px-1.5 py-0.5 rounded mt-0.5 inline-block"
                  style={{ background: color + "20", color }}
                >
                  {m.parti}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

// ── Page principale ───────────────────────────────────────────────────────────
export default function AnnuairePage() {
  const [deputes, setDeputes]   = useState<Depute[]>([]);
  const [partis, setPartis]     = useState<Parti[]>([]);
  const [ministres, setMinistres] = useState<Ministre[]>([]);
  const [recherche, setRecherche] = useState("");
  const [loading, setLoading]   = useState(true);
  const searchRef = useRef<HTMLInputElement>(null);
  const router_push = (url: string) => { window.location.href = url; };

  useEffect(() => {
    Promise.all([
      fetch(`${API}/deputes?limit=700`).then((r) => r.json()),
      fetch(`${API}/partis`).then((r) => r.json()),
      fetch(`${API}/gouvernement`).then((r) => r.json()),
    ]).then(([dep, par, gov]) => {
      setDeputes(dep.items ?? dep);
      setPartis(par);
      setMinistres(gov);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const resultats = useMemo(() => {
    if (!recherche.trim()) return [];
    const q = recherche.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    return deputes.filter((d) => {
      const full = `${d.prenom} ${d.nom}`.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      return full.includes(q);
    }).slice(0, 12);
  }, [deputes, recherche]);

  const totalDeputes = deputes.length;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-400">Chargement des données…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Navbar */}
      <nav className="sticky top-0 z-40 border-b border-slate-200/60 dark:border-slate-700/60 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-blue-900 rounded" />
            <span className="font-bold text-slate-900 dark:text-white text-lg tracking-tight">Lumin</span>
          </div>
          <div className="flex gap-6 text-sm font-medium text-slate-500 dark:text-slate-400">
            <a href="/" className="hover:text-slate-900 dark:hover:text-white transition-colors">Accueil</a>
            <a href="/annuaire" className="text-blue-600 dark:text-blue-400">Annuaire</a>
            <a href="/lois" className="hover:text-slate-900 dark:hover:text-white transition-colors">Lois</a>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-10 space-y-16">

        {/* ── HERO + HÉMICYCLE ────────────────────────────────────────────── */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
          <div>
            <p className="text-xs font-semibold tracking-widest text-blue-600 uppercase mb-3">
              XVIIe législature
            </p>
            <h1 className="text-4xl font-bold text-slate-900 dark:text-white leading-tight mb-4">
              L'hémicycle<br />en un regard
            </h1>
            <p className="text-slate-500 dark:text-slate-400 mb-8 leading-relaxed">
              {totalDeputes} députés, {partis.filter(p => p.nb_sieges > 0).length} groupes politiques.
              Explorez la composition de l'Assemblée nationale, les partis et leurs représentants.
            </p>

            {/* Stats rapides */}
            <div className="grid grid-cols-3 gap-4">
              {[
                { label: "Députés", value: totalDeputes },
                { label: "Groupes", value: partis.filter(p => p.nb_sieges > 0).length },
                { label: "Sièges total", value: 577 },
              ].map((s) => (
                <div key={s.label} className="bg-white dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-700/50 p-4">
                  <p className="text-2xl font-bold text-slate-900 dark:text-white">{s.value}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{s.label}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Hémicycle */}
          <div className="bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-100 dark:border-slate-700/50 p-6">
            <Hemicycle partis={partis} total={totalDeputes} />
            {/* Légende */}
            <div className="flex flex-wrap gap-2 mt-4 justify-center">
              {partis.filter(p => p.nb_sieges > 0).slice(0, 8).map((p) => (
                <div key={p.id} className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ background: p.couleur }} />
                  <span className="text-xs text-slate-500">{p.nom_court}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── RECHERCHE DÉPUTÉS ────────────────────────────────────────────── */}
        <section>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">
            Rechercher un député
          </h2>
          <div className="relative max-w-xl">
            <svg className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
            </svg>
            <input
              ref={searchRef}
              type="search"
              placeholder="Nom, prénom…"
              value={recherche}
              onChange={(e) => setRecherche(e.target.value)}
              className="w-full pl-10 pr-4 py-3 text-sm rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm"
            />
            {recherche && (
              <button onClick={() => setRecherche("")} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          {/* Résultats */}
          {resultats.length > 0 && (
            <div className="mt-3 max-w-xl bg-white dark:bg-slate-800/90 rounded-2xl border border-slate-100 dark:border-slate-700/50 shadow-xl overflow-hidden">
              {resultats.map((d) => <DeputeCard key={d.id} d={d} />)}
            </div>
          )}
          {recherche.length > 1 && resultats.length === 0 && (
            <p className="mt-3 text-sm text-slate-400">Aucun résultat pour « {recherche} »</p>
          )}
        </section>

        {/* ── PARTIS POLITIQUES ────────────────────────────────────────────── */}
        <section>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-6">
            Groupes politiques
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {partis.filter(p => p.nb_sieges > 0).map((parti) => (
              <PartiCard
                key={parti.id}
                parti={parti}
                onClick={() => router_push(`/partis/${parti.slug}`)}
              />
            ))}
          </div>
        </section>

        {/* ── GOUVERNEMENT ─────────────────────────────────────────────────── */}
        <GouvernementSection ministres={ministres} />

      </div>
    </div>
  );
}