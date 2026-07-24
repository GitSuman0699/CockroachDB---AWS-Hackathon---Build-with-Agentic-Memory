import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Mnemosyne - Agentic Memory",
  description: "A demonstration of episodic, semantic, procedural, and working memory.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} ${outfit.variable} antialiased bg-zinc-950 text-zinc-50 selection:bg-indigo-500/30 selection:text-indigo-200 min-h-screen`}
      >
        {children}
      </body>
    </html>
  );
}
