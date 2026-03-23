import type { Metadata } from 'next'
import { ThemeProvider } from '@/components/theme-provider'
import { KeyboardShortcutsHandler } from '@/components/keyboard-shortcuts-handler'

import './globals.css'

export const metadata: Metadata = {
  title: 'NetGuard - Network Malware Detection System',
  description: 'Real-time network-level malware detection and operating system protection dashboard',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans antialiased" suppressHydrationWarning>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <KeyboardShortcutsHandler />
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
