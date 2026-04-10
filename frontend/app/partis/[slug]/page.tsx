"use client";

import { useState, useEffect, useMemo } from "react";
import { use } from "react";

const API = "http://localhost:8000";

interface Depute {
  id: string; prenom: string; nom: string;
  groupe: string; circonscription: string; photo_url: string;
}
interface Parti {
  id: string; slug: string; nom: string; nom_court: string;
  couleur: string; description: string; valeurs: string[];
  nb_sieges: number; orientation: string; fondation: number;
  deputes: Depute[];
}

const COULEURS: Record<string, string> = {
  RN: "#003189", LR: "#0D47A1", HOR: "#1565C0", REN: "#FF6D00",
  MODEM: "#FF8F00", SOC: "#E91E63", ECO: "#2E7D32",
  LFI: "#B71C1C", GDR: "#C62828", LIOT: "#6A1B9A", NI: "#607D8B",
};

// ── Photo avec fallback ────────────────────────────────────────────────────
function Photo({ url, prenom, nom, groupe }: {
  url: string; prenom: string; nom: string; groupe: string;
}) {
  const [err, setErr] = useState(false);
  const color = COULEURS[groupe] ?? "#607D8B";
  const initiales = `${prenom[0] ?? ""}${nom[0] ?? ""}`.toUpperCase();

  if (err) {
    return (
      <div
        className="w-full h-full flex items-center justify-center text-white text-2xl font-bold"
        style={{ background: `linear-gradient(135deg, ${color}cc, ${color})` }}
      >
        {initiales}
      </div>
    );
  }
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={url} alt={`${prenom} ${nom}`}
      onError={() => setErr(true)}
      className="w-full h-full object-cover object-top"
    />
  );
}

// ── Card député ────────────────────────────────────────────────────────────
function DeputeMiniCard({ d, color }: { d: Depute; color: string }) {
  return (
    <div className="bg-white dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-700/50 overflow-hidden hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 cursor-pointer">
      <div className="h-32 overflow-hidden bg-slate-100 dark:bg-slate-700">
        <Photo url={d.photo_url} prenom={d.prenom} nom={d.nom} groupe={d.groupe} />
      </div>
      <div className="p-3">
        <p className="text-xs text-slate-400 font-medium">{d.prenom}</p>
        <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">{d.nom}</p>
        {d.circonscription && (
          <p className="text-xs text-slate-400 mt-0.5 truncate">{d.circonscription}</p>
        )}
      </div>
    </div>
  );
}

// ── Graphique barres horizontales ──────────────────────────────────────────
function StatsBar({ label, value, max, color }: {
  label: string; value: number; max: number; color: string;
}) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-slate-600 dark:text-slate-400">{label}</span>
        <span className="font-semibold text-slate-900 dark:text-white">{value}</span>
      </div>
      <div className="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-2">
        <div
          className="h-2 rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────
export default function PartiPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const [parti, setParti] = useState<Parti | null>(null);
  const [loading, setLoading] = useState(true);
  const [recherche, setRecherche] = useState("");
  const [departementFiltre, setDeptFiltre] = useState("");

  useEffect(() => {
    fetch(`${API}/partis/${slug}`)
      .then((r) => r.json())
      .then((d) => { setParti(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [slug]);

  const deputes = parti?.deputes ?? [];

  const deputesFiltres = useMemo(() => {
    const q = recherche.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    return deputes.filter((d) => {
      const full = `${d.prenom} ${d.nom}`.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      const matchNom = !q || full.includes(q);
      const matchDept = !departementFiltre || d.circonscription?.toLowerCase().includes(departementFiltre.toLowerCase());
      return matchNom && matchDept;
    });
  }, [deputes, recherche, departementFiltre]);

  // Stats : répartition par département
  const parDept = useMemo(() => {
    const map: Record<string, number> = {};
    deputes.forEach((d) => {
      if (!d.circonscription) return;
      const dept = d.circonscription.split(" - ")[0]?.trim() ?? d.circonscription;
      map[dept] = (map[dept] ?? 0) + 1;
    });
    return Object.entries(map)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8);
  }, [deputes]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!parti) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="text-center">
          <p className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Parti introuvable</p>
          <a href="/annuaire" className="text-blue-500 hover:underline">← Retour à l'annuaire</a>
        </div>
      </div>
    );
  }

  const color = parti.couleur;
  const pct = Math.round((parti.nb_sieges / 577) * 100);
  const maxDept = parDept[0]?.[1] ?? 1;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      {/* Navbar */}
      <nav className="sticky top-0 z-40 border-b border-slate-200/60 dark:border-slate-700/60 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center gap-4">
          <a href="/annuaire" className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Annuaire
          </a>
          <span className="text-slate-300 dark:text-slate-600">/</span>
          <span className="text-sm font-medium text-slate-900 dark:text-white">{parti.nom}</span>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-10 space-y-12">

        {/* ── EN-TÊTE ──────────────────────────────────────────────────────── */}
        <div className="relative overflow-hidden bg-white dark:bg-slate-800/60 rounded-3xl border border-slate-100 dark:border-slate-700/50 p-8">
          {/* Fond coloré décoratif */}
          <div
            className="absolute inset-0 opacity-5 dark:opacity-10"
            style={{ background: `radial-gradient(circle at 80% 50%, ${color}, transparent 60%)` }}
          />
          <div className="relative flex flex-col sm:flex-row gap-6 items-start">
            {/* Logo/sigle */}
            <div
              className="w-20 h-20 rounded-2xl flex items-center justify-center text-white font-black text-xl flex-shrink-0 shadow-lg"
              style={{ background: color }}
            >
              {parti.nom_court}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-3 mb-2">
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">{parti.nom}</h1>
                <span
                  className="text-sm font-medium px-3 py-1 rounded-full"
                  style={{ background: color + "20", color }}
                >
                  {parti.orientation}
                </span>
              </div>
              <p className="text-slate-500 dark:text-slate-400 mb-4 max-w-2xl leading-relaxed">
                {parti.description}
              </p>
              <div className="flex flex-wrap gap-6">
                <div>
                  <p className="text-3xl font-bold text-slate-900 dark:text-white">{parti.nb_sieges}</p>
                  <p className="text-xs text-slate-400">sièges ({pct}%)</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-slate-900 dark:text-white">{parti.fondation}</p>
                  <p className="text-xs text-slate-400">fondation</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-slate-900 dark:text-white">{deputes.length}</p>
                  <p className="text-xs text-slate-400">représentants</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── VALEURS + STATS ───────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Valeurs */}
          <div className="bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-100 dark:border-slate-700/50 p-6">
            <h2 className="text-base font-semibold text-slate-900 dark:text-white mb-5 flex items-center gap-2">
              <span className="w-5 h-5 rounded-md flex items-center justify-center text-xs" style={{ background: color + "20", color }}>★</span>
              Valeurs & engagements
            </h2>
            <div className="flex flex-wrap gap-2">
              {parti.valeurs.map((v) => (
                <span
                  key={v}
                  className="text-sm px-3 py-1.5 rounded-xl font-medium"
                  style={{ background: color + "15", color }}
                >
                  {v}
                </span>
              ))}
            </div>
          </div>

          {/* Présence par département */}
          <div className="bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-100 dark:border-slate-700/50 p-6">
            <h2 className="text-base font-semibold text-slate-900 dark:text-white mb-5 flex items-center gap-2">
              <span className="w-5 h-5 rounded-md flex items-center justify-center text-xs" style={{ background: color + "20", color }}>📍</span>
              Principaux départements
            </h2>
            {parDept.length > 0 ? (
              parDept.map(([dept, count]) => (
                <StatsBar key={dept} label={dept} value={count} max={maxDept} color={color} />
              ))
            ) : (
              <p className="text-sm text-slate-400">Aucune donnée de circonscription</p>
            )}
          </div>
        </div>

        {/* Barre hémicycle */}
        <div className="bg-white dark:bg-slate-800/60 rounded-2xl border border-slate-100 dark:border-slate-700/50 p-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">Poids à l'hémicycle</h2>
            <span className="text-2xl font-bold" style={{ color }}>{pct}%</span>
          </div>
          <div className="relative w-full bg-slate-100 dark:bg-slate-700 rounded-full h-4">
            <div
              className="h-4 rounded-full transition-all duration-1000"
              style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}aa, ${color})` }}
            />
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-xs text-slate-400">0</span>
            <span className="text-xs text-slate-400">{parti.nb_sieges} / 577 sièges</span>
            <span className="text-xs text-slate-400">577</span>
          </div>
        </div>

        {/* ── REPRÉSENTANTS ────────────────────────────────────────────────── */}
        <section>
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
              Représentants
              <span className="text-sm font-normal text-slate-400 ml-2">({deputesFiltres.length})</span>
            </h2>
            <div className="flex gap-2 w-full sm:w-auto">
              <div className="relative flex-1 sm:w-56">
                <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
                </svg>
                <input
                  type="search"
                  placeholder="Nom…"
                  value={recherche}
                  onChange={(e) => setRecherche(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-sm rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2"
                  style={{ "--tw-ring-color": color } as React.CSSProperties}
                />
              </div>
              <input
                type="search"
                placeholder="Département…"
                value={departementFiltre}
                onChange={(e) => setDeptFiltre(e.target.value)}
                className="w-36 px-3 py-2 text-sm rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2"
              />
            </div>
          </div>

          {deputesFiltres.length === 0 ? (
            <div className="text-center py-16 text-slate-400">
              <p>Aucun représentant trouvé pour ces critères.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
              {deputesFiltres.map((d) => (
                <DeputeMiniCard key={d.id} d={d} color={color} />
              ))}
            </div>
          )}
        </section>

      </div>
    </div>
  );
}