import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "API Contract Studio - Breaking Change Detection & Contract Testing",
  description: "Catch breaking API changes before they reach production. Open-source semantic diffing and automated contract validation for CI/CD.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full dark">
      <body className="min-h-full flex flex-col bg-[#090a0f] text-[#f8fafc]">
        <Navbar />
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
