import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'DocuScout',
  description: 'The Intelligent Risk Radar for Your Contracts & Documents',
  icons: {
    icon: '/icon.svg',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

