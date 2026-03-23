const backendApiUrl =
  process.env.BACKEND_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000"

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Performance & Build Optimization
  typescript: {
    ignoreBuildErrors: true,
  },
  
  // Compress responses
  compress: true,
  
  // Optimize images
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  

  // Code splitting & tree-shaking
  experimental: {
    optimizePackageImports: [
      '@radix-ui/react-dialog',
      '@radix-ui/react-dropdown-menu',
      '@radix-ui/react-select',
      '@radix-ui/react-tabs',
      '@radix-ui/react-tooltip',
      'lucide-react',
    ],
  },
  
  // Rewrite API calls
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendApiUrl}/api/:path*`,
      },
      {
        source: "/health",
        destination: `${backendApiUrl}/health`,
      },
    ]
  },
}

export default nextConfig
