'use client'

import { useState } from 'react'
import UploadModal from '@/components/UploadModal'
import PostIngestionPage from '@/components/PostIngestionPage'

export default function Home() {
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [isIngested, setIsIngested] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)

  const handleIngestionComplete = (newSessionId: string) => {
    setSessionId(newSessionId)
    setIsIngested(true)
    setShowUploadModal(false)
  }

  return (
    <div className="container">
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="32" height="32" rx="8" fill="#6366F1"/>
              <path d="M16 8L22 14L16 20L10 14L16 8Z" fill="white"/>
              <path d="M8 22L14 16L20 22L14 28L8 22Z" fill="white" opacity="0.8"/>
            </svg>
            <h1>DocuScout</h1>
          </div>
          <p className="tagline">The Intelligent Risk Radar for Your Contracts & Documents</p>
        </div>
      </header>

      <main className="main-content">
        {!isIngested ? (
          <div className="upload-container">
            <div className="upload-content">
              <h2>Upload Your Documents</h2>
              <p>Upload PDF files to analyze contracts and identify risks</p>
              <button 
                className="btn btn-primary btn-large"
                onClick={() => setShowUploadModal(true)}
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M10 2V14M4 8H16" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
                Upload PDFs
              </button>
            </div>
          </div>
        ) : (
          <PostIngestionPage sessionId={sessionId} />
        )}
      </main>

      {showUploadModal && (
        <UploadModal
          onClose={() => setShowUploadModal(false)}
          onIngestionComplete={handleIngestionComplete}
        />
      )}
    </div>
  )
}

