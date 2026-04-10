import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Lumin | La Vigie de l'Hémicycle",
  description: "Rendre la démocratie accessible grâce à l'IA — suivez vos députés, comprenez les lois.",
  openGraph: {
    title: "Lumin",
    description: "La politique française, décodée.",
    locale: "fr_FR",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className={inter.variable}>
      <body className="min-h-screen">
        <header className="fixed top-0 w-full z-50">
          {/* Barre principale */}
          <div className="border-b border-[var(--border)] bg-[var(--surface)]/80 backdrop-blur-xl">
            <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
              {/* Logo */}
              <a href="/" className="flex items-center gap-3 group">
                <div className="w-9 h-9 bg-[var(--blue)] rounded-xl flex items-center justify-center shadow-md group-hover:scale-105 transition-transform">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <span className="font-bold text-lg tracking-tight text-[var(--text-1)]">
                  Lumin
                </span>
              </a>

              {/* Navigation */}
              <nav className="hidden md:flex items-center gap-1">
                {[
                  { href: "/",          label: "Accueil" },
                  { href: "/annuaire",  label: "Annuaire" },
                  { href: "/lois",      label: "Lois" },
                ].map(({ href, label }) => (
                  <a
                    key={href}
                    href={href}
                    className="px-4 py-2 text-sm font-medium rounded-xl text-[var(--text-2)] hover:text-[var(--text-1)] hover:bg-[var(--surface-2)] transition-all"
                  >
                    {label}
                  </a>
                ))}
              </nav>

              {/* Actions */}
              <div className="flex items-center gap-3">
                {/* Indicateur live */}
                <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-100">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse-dot" />
                  <span className="text-xs font-medium text-emerald-700">Live</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        <main className="pt-16">
          {children}
        </main>
      </body>
    </html>
  );
}