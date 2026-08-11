import { NextResponse } from "next/server";
import { createClient } from "redis";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const email = searchParams.get("email");
  if (!email) {
    return NextResponse.json({ error: "Email is required" }, { status: 400 });
  }

  try {
    const redisHost = process.env.REDIS_HOST || "127.0.0.1";
    const redisPort = process.env.REDIS_PORT || "6379";
    const redisPassword = process.env.REDIS_PASSWORD || "redis_password";
    
    const client = createClient({
      url: `redis://:${redisPassword}@${redisHost}:${redisPort}`,
    });
    await client.connect();
    const otp = await client.get(`otp:${email}`);
    await client.disconnect();

    return NextResponse.json({ otp });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
