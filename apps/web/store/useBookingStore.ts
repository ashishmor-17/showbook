import { create } from "zustand";

interface BookingDetails {
  showtimeId: string;
  movieTitle: string;
  venueName: string;
  startTime: string;
  showDate: string;
  pricePerSeat: number;
}

interface BookingState {
  selectedSeats: string[];
  showtimeId: string | null;
  movieTitle: string | null;
  venueName: string | null;
  startTime: string | null;
  showDate: string | null;
  pricePerSeat: number;
  convenienceFee: number;
  
  setSelectedSeats: (seats: string[]) => void;
  setBookingDetails: (details: BookingDetails) => void;
  clearBooking: () => void;
}

export const useBookingStore = create<BookingState>((set) => ({
  selectedSeats: [],
  showtimeId: null,
  movieTitle: null,
  venueName: null,
  startTime: null,
  showDate: null,
  pricePerSeat: 0,
  convenienceFee: 20, // ₹20 convenience fee per ticket (2000 Paise)

  setSelectedSeats: (selectedSeats) => set({ selectedSeats }),
  
  setBookingDetails: (details) => set({
    showtimeId: details.showtimeId,
    movieTitle: details.movieTitle,
    venueName: details.venueName,
    startTime: details.startTime,
    showDate: details.showDate,
    pricePerSeat: details.pricePerSeat,
  }),

  clearBooking: () => set({
    selectedSeats: [],
    showtimeId: null,
    movieTitle: null,
    venueName: null,
    startTime: null,
    showDate: null,
    pricePerSeat: 0,
  }),
}));
