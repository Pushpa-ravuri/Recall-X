import type { Metadata } from "next";
import "./globals.css";
import Navbar from "../components/Navbar";

export const metadata: Metadata = {
  title: "RECALL-X | AI Operational Experience Memory",
  description: "AI Agent for Recovering Lost Operational Knowledge in Manufacturing",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-industrial-950 text-slate-100 min-h-screen flex flex-col antialiased selection:bg-cyan-500 selection:text-slate-950">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </main>
        <footer className="border-t border-industrial-800 bg-industrial-950 py-4 text-center text-xs font-mono text-slate-400">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
            <span>RECALL-X &copy; 2026 &mdash; AI Operational Experience Memory System</span>
            <span className="text-amber-400/80">
              Decision-Support System: Human Operator In The Loop
            </span>
          </div>
        </footer>
      </body>
    </html>
  );
}
