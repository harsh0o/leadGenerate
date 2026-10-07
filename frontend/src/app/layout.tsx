import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { PersonaProvider } from "@/providers/PersonaProvider";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "LeadHunter AI",
  description: "AI-powered lead generation across platforms",
  authors: [{ name: "harsh0o" }],
  generator: "leadhunter-ai/harsh0o",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-950 text-white flex h-screen overflow-hidden`}>
        <PersonaProvider>
          <Sidebar />
          <div className="flex-1 flex flex-col min-w-0">
            <Header />
            <main className="flex-1 overflow-auto p-4 md:p-6 lg:p-8">
              {children}
            </main>
          </div>
        </PersonaProvider>
      </body>
    </html>
  );
}
