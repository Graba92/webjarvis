import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "J.A.R.V.I.S. AI OS — CachyOS Edition",
  description: "Futuristic 3D Force-Directed Knowledge Graph & Gemini Live AI Operating System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="de" className="dark">
      <body className="bg-[#080a0f] text-[#f0f6fc] antialiased overflow-hidden select-none">
        <div className="absolute inset-0 scanlines z-50 pointer-events-none opacity-40" />
        {children}
      </body>
    </html>
  );
}
