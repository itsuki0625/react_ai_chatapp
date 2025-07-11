// import type { NextConfig } from "next"; // 型インポートを削除

const nextConfig = { // 型注釈を削除
  reactStrictMode: false,
  staticPageGenerationTimeout: 180,
  images: {
    domains: ['localhost', 'backend'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.amazonaws.com',
      },
      {
        protocol: 'https',
        hostname: 'docs.google.com',
      },
      {
        protocol: 'https',
        hostname: 'i.ytimg.com',
      },
      {
        protocol: 'https',
        hostname: 'img.youtube.com',
      },
      {
        protocol: 'https',
        hostname: 'speakerd.s3.amazonaws.com',
      },
      {
        protocol: 'https',
        hostname: 'image.slidesharecdn.com',
      },
      {
        protocol: 'https',
        hostname: 'drive.google.com',
      }
    ],
  },
  async rewrites() {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://backend:5050';
    return [
      // 広すぎる /api/:path* ルールを削除
      // {
      //   source: '/api/:path*',
      //   destination: `${apiBaseUrl}/api/:path*`,
      // },
      {
        source: '/api/v1/:path*', // バックエンドAPIはこのプレフィックスを想定
        destination: `${apiBaseUrl}/api/v1/:path*`,
      },
    ];
  },
  async redirects() {
    return [
      // URLパス内のアンダースコアをハイフンに統一 (永続リダイレクト)
      {
        source: '/chat/self_analysis/:sessionId*',
        destination: '/chat/self-analysis/:sessionId*',
        permanent: true,
      },
      {
        source: '/chat/study_support/:sessionId*',
        destination: '/chat/study-support/:sessionId*',
        permanent: true,
      },
      // 他の chatType も必要なら追加
      // {
      //   source: '/chat/admission_type/:sessionId*',
      //   destination: '/chat/admission-type/:sessionId*',
      //   permanent: true,
      // },
    ];
  },
  experimental: {
    // optimizeFonts: true, // このオプションはバージョンによって非推奨/削除の可能性
    scrollRestoration: true,
  },
};

export default nextConfig;
