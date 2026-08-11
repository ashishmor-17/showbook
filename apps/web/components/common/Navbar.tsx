"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore, City } from "../../store/useAuthStore";
import { venueApi, userApi } from "../../lib/api";
import { Film, MapPin, Search, User, LogOut, Ticket } from "lucide-react";

export default function Navbar() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const { user, accessToken, setUser, selectedCity, setCity, logout, hydrate, isHydrated } = useAuthStore();
  const [cities, setCities] = useState<City[]>([]);
  const [searchQuery, setSearchQuery] = useState(searchParams.get("q") || "");
  const [showDropdown, setShowDropdown] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (isHydrated && accessToken && !user) {
      userApi.getProfile()
        .then((res) => {
          const profile = res.data;
          setUser({
            id: profile.user_id,
            email: profile.email,
            name: profile.name || profile.email.split("@")[0],
          });
        })
        .catch((err) => {
          console.error("Failed to restore user profile session", err);
        });
    }
  }, [isHydrated, accessToken, user, setUser]);

  useEffect(() => {
    // Fetch available cities
    venueApi.getCities()
      .then((res) => {
        if (res.data?.cities) {
          setCities(res.data.cities);
          // Set default city if none is selected
          if (!selectedCity && res.data.cities.length > 0) {
            setCity(res.data.cities[0]);
          }
        }
      })
      .catch((err) => console.error("Error fetching cities", err));
  }, [selectedCity, setCity]);

  const handleCitySelect = (city: City) => {
    setCity(city);
    setShowDropdown(false);
    // Reload or redirect
    router.refresh();
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/?q=${encodeURIComponent(searchQuery.trim())}`);
    } else {
      router.push("/");
    }
  };

  return (
    <nav className="sticky top-0 z-50 glass-panel border-b border-zinc-800 px-4 md:px-8 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 text-xl font-bold tracking-wider text-brand-400 hover:opacity-90">
          <Film className="w-6 h-6 text-brand-500 animate-pulse-slow" />
          <span>SHOW<span className="text-foreground">BOOK</span></span>
        </Link>

        {/* City Selector */}
        <div className="relative">
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 hover:border-zinc-700 transition text-sm font-medium text-zinc-300"
          >
            <MapPin className="w-4 h-4 text-brand-400" />
            <span>{selectedCity?.name || "Select City"}</span>
          </button>

          {showDropdown && (
            <div className="absolute left-0 mt-2 w-48 rounded-lg bg-zinc-900 border border-zinc-800 shadow-2xl z-50 py-1">
              <div className="px-3 py-1.5 text-xs text-zinc-500 font-semibold border-b border-zinc-800">
                Popular Cities
              </div>
              {cities.map((city) => (
                <button
                  key={city.id}
                  onClick={() => handleCitySelect(city)}
                  className={`w-full text-left px-4 py-2 text-sm hover:bg-zinc-800 transition ${
                    selectedCity?.id === city.id ? "text-brand-400 font-medium" : "text-zinc-300"
                  }`}
                >
                  {city.name}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="hidden md:flex flex-1 max-w-md relative">
          <input
            type="text"
            placeholder="Search for movies, events, venues..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-zinc-900 border border-zinc-800 rounded-lg py-2 pl-4 pr-10 text-sm focus:outline-none focus:border-brand-500 transition text-zinc-200"
          />
          <button type="submit" className="absolute right-3 top-2.5 text-zinc-400 hover:text-foreground">
            <Search className="w-4 h-4" />
          </button>
        </form>

        {/* User / Action Buttons */}
        <div className="flex items-center gap-3">
          {isHydrated && user ? (
            <div className="relative">
              <button
                onClick={() => setShowProfileMenu(!showProfileMenu)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-zinc-900 transition text-sm font-medium text-zinc-300"
              >
                <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-white font-bold">
                  {String(user.name || user.email || "U").charAt(0).toUpperCase()}
                </div>
                <span className="hidden sm:inline">{user.name}</span>
              </button>

              {showProfileMenu && (
                <div className="absolute right-0 mt-2 w-48 rounded-lg bg-zinc-900 border border-zinc-800 shadow-2xl z-50 py-1">
                  <Link
                    href="/profile"
                    onClick={() => setShowProfileMenu(false)}
                    className="flex items-center gap-2 px-4 py-2.5 text-sm text-zinc-300 hover:bg-zinc-800 transition"
                  >
                    <User className="w-4 h-4" />
                    <span>My Profile</span>
                  </Link>
                  <Link
                    href="/bookings"
                    onClick={() => setShowProfileMenu(false)}
                    className="flex items-center gap-2 px-4 py-2.5 text-sm text-zinc-300 hover:bg-zinc-800 transition"
                  >
                    <Ticket className="w-4 h-4" />
                    <span>My Bookings</span>
                  </Link>
                  <hr className="border-zinc-800 my-1" />
                  <button
                    onClick={() => {
                      logout();
                      setShowProfileMenu(false);
                      router.push("/login");
                    }}
                    className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-red-400 hover:bg-zinc-800 transition text-left"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Logout</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <Link
              href="/login"
              className="px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 transition text-sm font-semibold text-white shadow-lg glow-primary"
            >
              Sign In
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
