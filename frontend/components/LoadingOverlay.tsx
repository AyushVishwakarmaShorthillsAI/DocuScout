'use client'

interface LoadingOverlayProps {
  message?: string
}

export default function LoadingOverlay({ message = 'Processing...' }: LoadingOverlayProps) {
  return (
    <div className="loading-overlay">
      <div className="spinner"></div>
      <p id="loadingMessage">{message}</p>
    </div>
  )
}

