import type { Metadata } from "next";
import "./globals.css";

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
      <body>{children}</body>
    </html>
  );
}
