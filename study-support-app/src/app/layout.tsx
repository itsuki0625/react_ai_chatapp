import '@/styles/globals.css'
import type { Metadata } from 'next'
import { Providers } from './providers'

export const metadata: Metadata = {
  title: 'SmartAo',
  description: 'AIを活用した学習支援アプリケーション',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}