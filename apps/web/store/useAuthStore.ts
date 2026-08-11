import { create } from "zustand";

export interface User {
  id: string;
  name: string;
  email: string;
}

export interface City {
  id: string;
  name: string;
  slug: string;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  selectedCity: City | null;
  isHydrated: boolean;
  setTokens: (accessToken: string, refreshToken: string) => void;
  setUser: (user: User | null) => void;
  setCity: (city: City | null) => void;
  logout: () => void;
  hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  selectedCity: null,
  isHydrated: false,

  setTokens: (accessToken, refreshToken) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("showbook_access_token", accessToken);
      localStorage.setItem("showbook_refresh_token", refreshToken);
      // Synchronize with cookie for Next.js routing middleware
      document.cookie = `showbook_access_token=${accessToken}; path=/; max-age=86400; SameSite=Lax`;
    }
    set({ accessToken, refreshToken });
  },

  setUser: (user) => {
    if (typeof window !== "undefined") {
      if (user) {
        localStorage.setItem("showbook_user", JSON.stringify(user));
      } else {
        localStorage.removeItem("showbook_user");
      }
    }
    set({ user });
  },

  setCity: (city) => {
    if (typeof window !== "undefined") {
      if (city) {
        localStorage.setItem("showbook_city", JSON.stringify(city));
      } else {
        localStorage.removeItem("showbook_city");
      }
    }
    set({ selectedCity: city });
  },

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("showbook_access_token");
      localStorage.removeItem("showbook_refresh_token");
      localStorage.removeItem("showbook_user");
      // Clear cookie for Next.js routing middleware
      document.cookie = "showbook_access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    }
    set({ accessToken: null, refreshToken: null, user: null });
  },

  hydrate: () => {
    if (typeof window === "undefined") return;
    
    const accessToken = localStorage.getItem("showbook_access_token");
    const refreshToken = localStorage.getItem("showbook_refresh_token");
    
    let user: User | null = null;
    const rawUser = localStorage.getItem("showbook_user");
    if (rawUser) {
      try {
        user = JSON.parse(rawUser);
      } catch (_) {}
    }

    let selectedCity: City | null = null;
    const rawCity = localStorage.getItem("showbook_city");
    if (rawCity) {
      try {
        selectedCity = JSON.parse(rawCity);
      } catch (_) {}
    }

    set({
      accessToken,
      refreshToken,
      user,
      selectedCity,
      isHydrated: true,
    });
  },
}));
