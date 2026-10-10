/** @type {import('next').NextConfig} */
// Base path is env-configurable via NEXT_PUBLIC_BASE_PATH (e.g. /rag).
// Change requires restarting `npm run dev` / rebuilding.
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '/rag';

const nextConfig = {
  basePath: basePath || undefined,
};

export default nextConfig;
