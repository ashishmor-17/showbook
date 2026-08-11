import axios from "axios";
import { useAuthStore } from "../store/useAuthStore";

const api = axios.create({
  baseURL: "", // Using relative URLs because of Next.js rewrites
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to attach JWT tokens and X-User-Id
api.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const accessToken = localStorage.getItem("showbook_access_token");
      if (accessToken) {
        config.headers.Authorization = `Bearer ${accessToken}`;
      }
      
      const rawUser = localStorage.getItem("showbook_user");
      if (rawUser) {
        try {
          const user = JSON.parse(rawUser);
          if (user?.id) {
            config.headers["X-User-Id"] = user.id;
          }
        } catch (_) {}
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle auto 401 refresh token
let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = localStorage.getItem("showbook_refresh_token");
        if (!refreshToken) {
          throw new Error("No refresh token available");
        }

        const resp = await axios.post("/auth/api/v1/auth/refresh", {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token } = resp.data;
        useAuthStore.getState().setTokens(access_token, refresh_token);
        
        processQueue(null, access_token);
        isRefreshing = false;

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        isRefreshing = false;
        useAuthStore.getState().logout();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// API Functions
export const authApi = {
  register: (payload: any) => api.post("/auth/api/v1/auth/register", payload),
  verifyOtp: (payload: any) => api.post("/auth/api/v1/auth/verify-otp", payload),
  login: (payload: any) => api.post("/auth/api/v1/auth/login", payload),
  me: () => api.get("/auth/api/v1/auth/me"),
  getDevOtp: (email: string) => axios.get(`/api/dev/otp?email=${encodeURIComponent(email)}`),
};

export const userApi = {
  getProfile: () => api.get("/users/api/v1/users/me"),
  updateProfile: (payload: any) => api.patch("/users/api/v1/users/me", payload),
};

export const venueApi = {
  getCities: () => api.get("/venues/api/v1/venues/cities"),
  getVenues: (citySlug: string) => api.get(`/venues/api/v1/venues/cities/${citySlug}/venues`),
  getShowtimes: (params: { catalog_ref_id: string; catalog_type: string; city_id: string; date: string }) =>
    api.get("/venues/api/v1/venues/showtimes", { params }),
  getShowtimeDetails: (showtimeId: string) => api.get(`/venues/api/v1/venues/showtimes/${showtimeId}`),
  getSeats: (showtimeId: string) => api.get(`/venues/api/v1/venues/showtimes/${showtimeId}/seats`),
};

export const catalogApi = {
  getMovies: (params?: any) => api.get("/catalog/api/v1/catalog/movies", { params }),
  getMovie: (slug: string) => api.get(`/catalog/api/v1/catalog/movies/${slug}`),
  getMovieById: (id: string) => api.get(`/catalog/api/v1/catalog/movies/id/${id}`),
  searchMovies: (params: { q: string; city_id?: string; type?: string }) =>
    api.get("/catalog/api/v1/catalog/search", { params: { type: "MOVIE", ...params } }),
};

export const bookingApi = {
  initiate: (payload: { showtime_id: string; seat_codes: string[]; idempotency_key?: string }) =>
    api.post("/bookings/api/v1/bookings/initiate", payload),
  get: (ref: string) => api.get(`/bookings/api/v1/bookings/${ref}`),
  cancel: (ref: string) => api.post(`/bookings/api/v1/bookings/${ref}/cancel`),
  list: (params?: any) => api.get("/bookings/api/v1/bookings", { params }),
};

export const paymentApi = {
  initiate: (payload: { booking_ref: string; gateway: string }) =>
    api.post("/payments/api/v1/payments/initiate", payload),
  getStatus: (txnId: string) => api.get(`/payments/api/v1/payments/${txnId}`),
  callback: (payload: any) => api.post("/payments/api/v1/payments/callback", payload),
};

export default api;
