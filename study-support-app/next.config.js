/** @type {import('next').NextConfig} */
const nextConfig = {
  // リアクトの厳格モードを有効化
  reactStrictMode: true,
  
  // 静的生成のタイムアウト設定
  staticPageGenerationTimeout: 180, // 3分
  
  // Swcの最適化を有効化
  swcMinify: true,
  
  // 画像最適化ドメインの設定
  images: {
    domains: ['localhost', 'backend'],
    // リモートパターンを追加して外部画像を許可
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.amazonaws.com',
      },
    ],
  },
  
  // API リライト設定
  async rewrites() {
    // 環境に応じたAPIベースURLを設定
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://backend:5050';
    
    return [
      {
        source: '/api/:path*',
        destination: `${apiBaseUrl}/api/:path*`,
        has: [
          {
            type: 'header',
            key: 'x-skip-next-auth',
            value: '(?!true)',
          },
        ],
      },
      {
        source: '/api/v1/:path*',
        destination: `${apiBaseUrl}/api/v1/:path*`,
      },
    ];
  },
  
  // 動的インポートの最適化
  experimental: {
    // フォールバックを強化
    optimizeFonts: true,
    scrollRestoration: true,
  },
};

module.exports = nextConfig; 