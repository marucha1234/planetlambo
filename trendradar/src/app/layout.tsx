import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TrendRadar",
  description:
    "Detector de tendencias tempranas de TikTok para planners y equipos de marca",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className="dark">
      <body>
        <header className="border-b border-terminal-border px-4 py-2 flex items-baseline gap-3">
          <span className="text-terminal-amber font-bold tracking-widest">
            TRENDRADAR
          </span>
          <span className="text-terminal-dim text-xs">
            señales tempranas · TikTok · AR MX BR ES US
          </span>
        </header>
        <main className="p-4">{children}</main>
      </body>
    </html>
  );
}
