'use client'

import { useEffect } from 'react'

interface NotificationProps {
  message: string
  type: 'success' | 'error'
  onClose: () => void
}

export default function Notification({ message, type, onClose }: NotificationProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose()
    }, 3000)

    return () => clearTimeout(timer)
  }, [onClose])

  return (
    <div className={`notification ${type}`}>
      {message}
    </div>
  )
}

