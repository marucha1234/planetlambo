/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      // covers de videos y sonidos servidos por el CDN de TikTok
      { protocol: "https", hostname: "**.tiktokcdn.com" },
      { protocol: "https", hostname: "**.tiktokcdn-us.com" },
    ],
  },
};

export default nextConfig;
