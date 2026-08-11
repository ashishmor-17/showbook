/** @type {import('next').NextConfig} */
const gatewayUrl = process.env.GATEWAY_URL || (process.env.NODE_ENV === "production" ? "http://api-gateway" : "http://127.0.0.1");

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/auth/:path*",
        destination: `${gatewayUrl}/auth/:path*`,
      },
      {
        source: "/users/:path*",
        destination: `${gatewayUrl}/users/:path*`,
      },
      {
        source: "/catalog/:path*",
        destination: `${gatewayUrl}/catalog/:path*`,
      },
      {
        source: "/venues/:path*",
        destination: `${gatewayUrl}/venues/:path*`,
      },
      {
        source: "/bookings/:path*",
        destination: `${gatewayUrl}/bookings/:path*`,
      },
      {
        source: "/payments/:path*",
        destination: `${gatewayUrl}/payments/:path*`,
      },
    ];
  },
};

export default nextConfig;
