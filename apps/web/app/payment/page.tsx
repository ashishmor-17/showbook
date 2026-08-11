"use client";

import React, { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "../../store/useAuthStore";
import { paymentApi, bookingApi } from "../../lib/api";
import axios from "axios";
import { ShieldAlert, CreditCard, Lock, ArrowLeft, CheckCircle, Clock } from "lucide-react";
import { Skeleton } from "../../components/ui/Skeleton";

function PaymentContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const bookingRef = searchParams.get("booking_ref");
  const amountPaise = searchParams.get("amount");
  
  const { user, hydrate } = useAuthStore();
  const [booking, setBooking] = useState<any>(null);
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [cardNumber, setCardNumber] = useState("");
  const [cardName, setCardName] = useState("");
  const [expiry, setExpiry] = useState("");
  const [cvv, setCvv] = useState("");
  const [cardType, setCardType] = useState("VISA");

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (!bookingRef) return;
    bookingApi.get(bookingRef)
      .then(res => {
        const b = res.data?.data || res.data;
        setBooking(b);
      })
      .catch(err => {
        console.error("Failed to fetch booking details", err);
      });
  }, [bookingRef]);

  useEffect(() => {
    if (!booking?.expires_at) return;

    const targetTime = new Date(booking.expires_at).getTime();

    const updateTimer = () => {
      const now = new Date().getTime();
      const difference = targetTime - now;

      if (difference <= 0) {
        setTimeLeft(0);
        router.push(`/booking/failed?ref=${bookingRef}`);
      } else {
        setTimeLeft(Math.floor(difference / 1000));
      }
    };

    updateTimer();
    const timerInterval = setInterval(updateTimer, 1000);

    return () => clearInterval(timerInterval);
  }, [booking?.expires_at, bookingRef, router]);

  useEffect(() => {
    const cleanNum = cardNumber.replace(/\s/g, "");
    if (cleanNum.startsWith("4")) setCardType("VISA");
    else if (cleanNum.startsWith("5")) setCardType("MASTERCARD");
    else if (cleanNum.startsWith("3")) setCardType("AMEX");
  }, [cardNumber]);

  const handleCardNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const digits = e.target.value.replace(/\D/g, "");
    const trimmed = digits.substring(0, 16);
    const matches = trimmed.match(/.{1,4}/g);
    setCardNumber(matches ? matches.join(" ") : trimmed);
  };

  const handleExpiryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = e.target.value.replace(/\D/g, "");
    if (val.length > 4) {
      val = val.substring(0, 4);
    }
    if (val.length > 2) {
      val = `${val.slice(0, 2)}/${val.slice(2)}`;
    }
    setExpiry(val);
  };

  const handlePay = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!bookingRef || !amountPaise || !user) return;

    // Validation: Card Number
    const cleanedCardNumber = cardNumber.replace(/\s/g, "");
    if (cleanedCardNumber.length !== 16) {
      setError("Card Number must be exactly 16 digits.");
      return;
    }

    // Validation: Cardholder Name
    const cleanedName = cardName.trim();
    if (cleanedName.length < 2) {
      setError("Cardholder Name must be at least 2 characters.");
      return;
    }
    if (!/^[a-zA-Z\s]+$/.test(cleanedName)) {
      setError("Cardholder Name must contain only letters and spaces.");
      return;
    }

    // Validation: Expiry Date
    if (!/^\d{2}\/\d{2}$/.test(expiry)) {
      setError("Expiry Date must be in MM/YY format.");
      return;
    }
    const [monthStr, yearStr] = expiry.split("/");
    const month = parseInt(monthStr, 10);
    const year = parseInt(`20${yearStr}`, 10);
    const now = new Date();
    const currentMonth = now.getMonth() + 1; // 1-12
    const currentYear = now.getFullYear();

    if (month < 1 || month > 12) {
      setError("Expiry month must be between 01 and 12.");
      return;
    }

    if (year < currentYear || (year === currentYear && month < currentMonth)) {
      setError("The card has already expired.");
      return;
    }

    // Validation: CVV
    if (cvv.length !== 3) {
      setError("CVV must be exactly 3 digits.");
      return;
    }

    setLoading(true);
    try {
      // 1. Initiate payment txn in DB
      const initRes = await paymentApi.initiate({
        booking_ref: bookingRef,
        gateway: "MOCK_STRIPE",
      });
      const paymentTxnId = initRes.data.payment_txn_id;

      // 2. Post callback to Next.js dev helper API to calculate signature and invoke webhook
      const callbackPayload = {
        payment_txn_id: paymentTxnId,
        booking_ref: bookingRef,
        user_id: user.id,
        gateway: "MOCK_STRIPE",
        gateway_txn_id: `ch_${Math.random().toString(36).substring(2, 10).toUpperCase()}`,
        amount: parseFloat(amountPaise) / 100.0,
        status: "SUCCESS",
      };

      const cbRes = await axios.post("/api/dev/pay-callback", callbackPayload);
      
      if (cbRes.data.success) {
        // Redirect to booking success
        router.push(`/booking/success?ref=${bookingRef}`);
      } else {
        router.push(`/booking/failed?ref=${bookingRef}`);
      }
    } catch (err: any) {
      console.error(err);
      router.push(`/booking/failed?ref=${bookingRef}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!bookingRef) return;
    try {
      router.push("/");
    } catch (_) {}
  };

  if (!bookingRef || !amountPaise) {
    return (
      <div className="max-w-md mx-auto px-4 py-20 text-center flex flex-col items-center gap-4">
        <ShieldAlert className="w-12 h-12 text-red-400" />
        <h3 className="text-xl font-bold text-white">Invalid Payment Request</h3>
        <p className="text-sm text-zinc-500">The checkout session params are missing.</p>
        <Link href="/" className="px-5 py-2.5 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 hover:bg-zinc-800 transition">
          Back to Home
        </Link>
      </div>
    );
  }

  const amountRupees = parseFloat(amountPaise) / 100.0;

  return (
    <div className="max-w-md mx-auto px-4 py-10 flex flex-col gap-6 w-full text-left">
      {/* Header */}
      <div className="flex flex-col gap-2">
        <button onClick={handleCancel} className="flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white transition w-fit font-medium">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Cancel & Return</span>
        </button>
        <h1 className="text-2xl font-black text-white mt-2">Secure Payment Gateway</h1>
        
        {timeLeft !== null && (
          <div className={`flex items-center justify-between p-3 rounded-lg border text-sm font-bold mt-2 ${
            timeLeft < 60 
              ? "bg-red-950/40 border-red-800 text-red-400 animate-pulse" 
              : "bg-zinc-900 border-zinc-800 text-zinc-300"
          }`}>
            <span className="flex items-center gap-1.5">
              <Clock className="w-4 h-4" />
              <span>Time Remaining to Pay</span>
            </span>
            <span className="font-mono text-base">
              {Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, "0")}
            </span>
          </div>
        )}

        <div className="flex justify-between items-center bg-zinc-900 border border-zinc-800 p-4 rounded-xl mt-1">
          <span className="text-xs text-zinc-400">Total Payable</span>
          <span className="text-xl font-black text-brand-400">₹{amountRupees.toFixed(2)}</span>
        </div>
      </div>

      {/* Credit Card Graphic Card representation */}
      <div className="relative aspect-[1.586/1] w-full rounded-2xl p-6 overflow-hidden bg-gradient-to-br from-brand-700 via-brand-600 to-zinc-900 shadow-2xl glow-primary flex flex-col justify-between border border-white/10">
        <div className="flex justify-between items-start">
          <div className="flex flex-col">
            <span className="text-[10px] text-brand-200 uppercase tracking-widest font-semibold">ShowBook Card</span>
            <CreditCard className="w-8 h-8 text-white mt-1" />
          </div>
          <span className="text-xs font-black text-white bg-white/10 px-2 py-0.5 rounded backdrop-blur">
            {cardType}
          </span>
        </div>

        <div className="flex flex-col gap-4">
          <span className="text-base md:text-lg font-mono text-white tracking-widest">
            {cardNumber || "•••• •••• •••• ••••"}
          </span>
          <div className="flex justify-between items-end">
            <div className="flex flex-col">
              <span className="text-[8px] text-brand-200 uppercase font-semibold">Card Holder</span>
              <span className="text-xs font-bold text-white uppercase">{cardName || "Customer Name"}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[8px] text-brand-200 uppercase font-semibold">Expiry</span>
              <span className="text-xs font-bold text-white">{expiry || "MM/YY"}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Inputs Form */}
      <form onSubmit={handlePay} className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl flex flex-col gap-4">
        {/* Card Number */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Card Number</label>
          <input
            type="text"
            required
            maxLength={19}
            placeholder="4111 2222 3333 4444"
            value={cardNumber}
            onChange={handleCardNumberChange}
            className="bg-zinc-950 border border-zinc-800 rounded-lg p-2.5 text-sm focus:outline-none focus:border-brand-500 text-zinc-200 font-mono"
          />
        </div>

        {/* Name */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Cardholder Name</label>
          <input
            type="text"
            required
            placeholder="John Doe"
            value={cardName}
            onChange={(e) => setCardName(e.target.value.replace(/[^a-zA-Z\s]/g, ""))}
            className="bg-zinc-950 border border-zinc-800 rounded-lg p-2.5 text-sm focus:outline-none focus:border-brand-500 text-zinc-200"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Expiry */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Expiry Date</label>
            <input
              type="text"
              required
              maxLength={5}
              placeholder="MM/YY"
              value={expiry}
              onChange={handleExpiryChange}
              className="bg-zinc-950 border border-zinc-800 rounded-lg p-2.5 text-sm focus:outline-none focus:border-brand-500 text-zinc-200 font-mono"
            />
          </div>

          {/* CVV */}
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-bold text-zinc-400 uppercase tracking-wider">CVV</label>
            <input
              type="password"
              required
              maxLength={3}
              placeholder="•••"
              value={cvv}
              onChange={(e) => setCvv(e.target.value.replace(/\D/g, "").substring(0, 3))}
              className="bg-zinc-950 border border-zinc-800 rounded-lg p-2.5 text-sm focus:outline-none focus:border-brand-500 text-zinc-200 font-mono"
            />
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-3 rounded-lg border bg-red-950/40 border-red-800 text-red-400 text-xs font-semibold">
            <ShieldAlert className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full mt-2 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 transition text-sm font-extrabold text-white flex items-center justify-center gap-2 shadow-xl glow-primary"
        >
          {loading ? (
            <span>Processing SAGA Payment...</span>
          ) : (
            <>
              <Lock className="w-4 h-4 text-emerald-400" />
              <span>Pay Securely ₹{amountRupees.toFixed(2)}</span>
            </>
          )}
        </button>

        <div className="flex items-center gap-1.5 justify-center text-[10px] text-zinc-500 mt-2">
          <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />
          <span>PCI-DSS Compliant 256-bit SSL Encryption</span>
        </div>
      </form>
    </div>
  );
}

export default function PaymentPage() {
  return (
    <Suspense fallback={
      <div className="max-w-md mx-auto px-4 py-10 w-full flex flex-col gap-6">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-44 w-full rounded-2xl" />
        <Skeleton className="h-80 w-full rounded-2xl" />
      </div>
    }>
      <PaymentContent />
    </Suspense>
  );
}
