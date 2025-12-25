'use client'

import { useState, useRef } from 'react'
import { apiClient } from '@/lib/api'
import LoadingOverlay from './LoadingOverlay'
import Notification from './Notification'

interface UploadModalProps {
  onClose: () => void
  onIngestionComplete: (sessionId: string) => void
}

export default function UploadModal({ onClose, onIngestionComplete }: UploadModalProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return
    
    const pdfFiles = Array.from(files).filter(file => 
      file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
    )
    
    setSelectedFiles(prev => {
      const newFiles = pdfFiles.filter(file => 
        !prev.find(f => f.name === file.name && f.size === file.size)
      )
      return [...prev, ...newFiles]
    })
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
    handleFileSelect(e.dataTransfer.files)
  }

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleIngest = async () => {
    if (selectedFiles.length === 0 || isLoading) return

    setIsLoading(true)
    setNotification(null)

    try {
      const response = await apiClient.ingestDocuments(selectedFiles)
      
      if (response.success && response.session_id) {
        setNotification({ message: 'Documents ingested successfully!', type: 'success' })
        setTimeout(() => {
          onIngestionComplete(response.session_id!)
        }, 1000)
      } else {
        setNotification({ 
          message: response.error || 'Ingestion failed', 
          type: 'error' 
        })
      }
    } catch (error: any) {
      setNotification({ 
        message: error.message || 'Failed to ingest documents', 
        type: 'error' 
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <>
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3>Upload PDF Files</h3>
            <button className="modal-close" onClick={onClose}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </button>
          </div>
          <div className="modal-body">
            <div 
              className={`drop-zone ${isDragOver ? 'drag-over' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="drop-zone-content">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
                </svg>
                <p className="drop-zone-text">Drag & drop PDF files here</p>
                <p className="drop-zone-hint">or</p>
                <button 
                  className="btn btn-secondary"
                  onClick={() => fileInputRef.current?.click()}
                >
                  Select Files
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf"
                  style={{ display: 'none' }}
                  onChange={(e) => handleFileSelect(e.target.files)}
                />
              </div>
            </div>

            {selectedFiles.length > 0 && (
              <div className="selected-files">
                <h4>Selected Files:</h4>
                <ul>
                  {selectedFiles.map((file, index) => (
                    <li key={index}>
                      <span>{file.name}</span>
                      <button 
                        className="remove-file"
                        onClick={() => removeFile(index)}
                      >
                        ×
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="modal-actions">
              <button 
                className="btn btn-primary btn-large"
                onClick={handleIngest}
                disabled={selectedFiles.length === 0 || isLoading}
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M10 2V14M4 8H16" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
                Ingest Documents
              </button>
            </div>
          </div>
        </div>
      </div>

      {isLoading && (
        <LoadingOverlay message="Uploading and ingesting documents... This may take a few minutes." />
      )}

      {notification && (
        <Notification
          message={notification.message}
          type={notification.type}
          onClose={() => setNotification(null)}
        />
      )}
    </>
  )
}

