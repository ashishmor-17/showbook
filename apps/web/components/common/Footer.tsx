import React from "react";
import Link from "next/link";
import { Film } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-zinc-800 bg-zinc-950 text-zinc-400 py-12 px-4 md:px-8 mt-auto">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* Info Column */}
        <div className="flex flex-col gap-4">
          <Link href="/" className="flex items-center gap-2 text-xl font-bold tracking-wider text-brand-400">
            <Film className="w-6 h-6 text-brand-500" />
            <span>SHOW<span className="text-foreground">BOOK</span></span>
          </Link>
          <p className="text-sm text-zinc-500">
            Premium entertainment ticket booking system. Explore showtimes, pick your seats, and get digital tickets instantly.
          </p>
        </div>

        {/* Categories */}
        <div>
          <h4 className="text-white font-semibold mb-4 text-sm tracking-wider uppercase">Catalog</h4>
          <ul className="space-y-2 text-sm">
            <li><Link href="/" className="hover:text-white transition">Now Showing</Link></li>
            <li><Link href="/" className="hover:text-white transition">Upcoming Movies</Link></li>
            <li><Link href="/" className="hover:text-white transition">Events & Theater</Link></li>
          </ul>
        </div>

        {/* Support */}
        <div>
          <h4 className="text-white font-semibold mb-4 text-sm tracking-wider uppercase">Support</h4>
          <ul className="space-y-2 text-sm">
            <li><Link href="/" className="hover:text-white transition">Help Center</Link></li>
            <li><Link href="/" className="hover:text-white transition">Terms & Conditions</Link></li>
            <li><Link href="/" className="hover:text-white transition">Privacy Policy</Link></li>
          </ul>
        </div>

        {/* Dev Mode Banner */}
        <div>
          <h4 className="text-white font-semibold mb-4 text-sm tracking-wider uppercase">Dev Panel</h4>
          <div className="rounded-lg bg-zinc-900 border border-zinc-800 p-4">
            <p className="text-xs text-zinc-500 mb-2 leading-relaxed">
              ShowBook Sandbox Admin controls can be simulated via API callbacks.
            </p>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-brand-900 text-brand-200">
              Local Dev Mode
            </span>
          </div>
        </div>
      </div>
      <div className="max-w-7xl mx-auto border-t border-zinc-900 mt-8 pt-8 flex flex-col sm:flex-row justify-between text-xs text-zinc-600 gap-4">
        <span>&copy; {new Date().getFullYear()} ShowBook Inc. All rights reserved.</span>
        <div className="flex gap-4">
          <Link href="/" className="hover:text-zinc-400 transition">Feedback</Link>
          <Link href="/" className="hover:text-zinc-400 transition">Contact Us</Link>
        </div>
      </div>
    </footer>
  );
}
