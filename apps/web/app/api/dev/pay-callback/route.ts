import { NextResponse } from "next/server";
import crypto from "crypto";

export async function POST(request: Request) {
  try {
    const payload = await request.json();
    const secret = "payment_gateway_secret_key";
    
    // Sort keys alphabetically and construct key1=value1&key2=value2, ignoring signature
    const orderedItems = Object.keys(payload)
      .filter((k) => k !== "signature")
      .sort()
      .map((k) => {
        let val = payload[k];
        if (k === "amount") {
          const num = Number(val);
          val = num % 1 === 0 ? num.toFixed(1) : num.toString();
        }
        return `${k}=${val}`;
      });
    
    const message = orderedItems.join("&");
    
    const signature = crypto
      .createHmac("sha256", secret)
      .update(message)
      .digest("hex");
    
    // Send callback to the backend payment service gateway callback handler
    const gatewayUrl = process.env.GATEWAY_URL || (process.env.NODE_ENV === "production" ? "http://api-gateway" : "http://localhost");
    const response = await fetch(`${gatewayUrl}/payments/api/v1/payments/callback`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...payload,
        signature,
      }),
    });
    
    const data = await response.json();
    return NextResponse.json({ 
      success: response.ok, 
      status: response.status,
      data 
    });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
