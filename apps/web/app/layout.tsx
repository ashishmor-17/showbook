import React, { Suspense } from "react";
import type { Metadata } from "next";
import "./globals.css";
import QueryProvider from "../components/common/QueryProvider";
import Navbar from "../components/common/Navbar";
import Footer from "../components/common/Footer";

export const metadata: Metadata = {
  title: "ShowBook - Premium Cinema Booking",
  description: "Book tickets for your favorite movies, events, and venues instantly.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="flex flex-col min-h-screen bg-background text-foreground">
        <QueryProvider>
          <Suspense fallback={<div className="h-16 bg-zinc-950 border-b border-zinc-800 animate-pulse" />}>
            <Navbar />
          </Suspense>
          <main className="flex-grow flex flex-col">
            {children}
          </main>
          <Footer />
        </QueryProvider>
      </body>
    </html>
  );
}
