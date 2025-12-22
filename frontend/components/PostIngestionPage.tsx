'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'

interface PostIngestionPageProps {
  sessionId: string | null
}

export default function PostIngestionPage({ sessionId }: PostIngestionPageProps) {
  const [qaMessages, setQaMessages] = useState<Array<{ sender: string; text: string; time: string; isProcessing?: boolean }>>([])
  const [qaInput, setQaInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  
  // Predict Warnings state
  const [isPredicting, setIsPredicting] = useState(false)
  const [progressMessage, setProgressMessage] = useState<string>('')
  const [showReportPopup, setShowReportPopup] = useState(false)
  const [reportContent, setReportContent] = useState<string>('')
  const [hasReport, setHasReport] = useState(false) // Track if report is ready

  const handleQASend = async () => {
    const query = qaInput.trim()
    if (!query || isLoading) return

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    
    // Add user message immediately
    setQaMessages(prev => [...prev, { sender: 'You', text: query, time }])
    
    // Clear input and set loading state
    const queryToSend = qaInput.trim()
    setQaInput('')
    setIsLoading(true)

    // Backend uses global session (sessionId parameter is optional and ignored)
    console.log('[PostIngestionPage] Sending Q&A request (using global session)')

    try {
      const response = await apiClient.chat(queryToSend)  // Backend uses global session automatically
      
      if (response.success && response.response) {
        setQaMessages(prev => [...prev, { 
          sender: 'DocuScout', 
          text: response.response!, 
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }])
      } else {
        setQaMessages(prev => [...prev, { 
          sender: 'DocuScout', 
          text: response.error || 'I encountered an error. Please try again.', 
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }])
      }
    } catch (error: any) {
      setQaMessages(prev => [...prev, { 
        sender: 'DocuScout', 
        text: error.message || 'Failed to get response. Please try again.', 
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handlePredictWarnings = async () => {
    // If report exists, show it instead of regenerating
    if (hasReport && reportContent) {
      setShowReportPopup(true)
      return
    }
    
    if (isPredicting) return
    
    setIsPredicting(true)
    setProgressMessage('Starting analysis... This may take several minutes.')
    setShowReportPopup(false)
    setReportContent('')
    setHasReport(false)
    
    try {
      // Call the predict warnings API
      // The backend will log progress at each step
      const response = await apiClient.predictWarnings(sessionId)
      
      if (response.success && response.report) {
        setReportContent(response.report)
        setHasReport(true) // Mark report as ready
        setProgressMessage('') // Clear progress message
      } else {
        const errorMsg = response.error || 'Failed to generate report'
        const step = response.step ? ` (Failed at: ${response.step})` : ''
        setProgressMessage(`Error: ${errorMsg}${step}`)
        setHasReport(false)
        alert(`Failed to generate report: ${errorMsg}${step}`)
      }
    } catch (error: any) {
      const errorMsg = error.message || 'An unexpected error occurred'
      setProgressMessage(`Error: ${errorMsg}`)
      setHasReport(false)
      alert(`Failed to generate report: ${errorMsg}`)
    } finally {
      setIsPredicting(false)
    }
  }
  
  // Simple markdown formatter (basic implementation)
  const formatMarkdown = (markdown: string): string => {
    if (!markdown) return ''
    
    // Escape HTML first
    let html = markdown
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
    
    // Headers (process in order from most to least specific)
    html = html.replace(/^#### (.*$)/gim, '<h4>$1</h4>')
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>')
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>')
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>')
    
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    
    // Italic (but not if it's part of bold)
    html = html.replace(/(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)/gim, '<em>$1</em>')
    
    // Code blocks (before inline code)
    html = html.replace(/```([\s\S]*?)```/gim, '<pre><code>$1</code></pre>')
    html = html.replace(/`([^`]+)`/gim, '<code>$1</code>')
    
    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    
    // Horizontal rules
    html = html.replace(/^---$/gim, '<hr>')
    
    // Lists (unordered)
    html = html.replace(/^\* (.*$)/gim, '<li>$1</li>')
    html = html.replace(/^- (.*$)/gim, '<li>$1</li>')
    // Lists (ordered)
    html = html.replace(/^(\d+)\. (.*$)/gim, '<li>$2</li>')
    
    // Wrap consecutive list items in ul
    html = html.replace(/(<li>.*<\/li>(\n|$))+/gim, (match) => {
      return '<ul>' + match.trim() + '</ul>'
    })
    
    // Paragraphs (split by double newlines)
    const paragraphs = html.split(/\n\n+/)
    html = paragraphs.map(p => {
      p = p.trim()
      if (!p) return ''
      // Don't wrap if it's already a block element
      if (p.match(/^<(h[1-6]|ul|ol|pre|hr)/)) return p
      return '<p>' + p + '</p>'
    }).join('')
    
    // Line breaks (single newlines)
    html = html.replace(/\n/gim, '<br>')
    
    return html
  }

  return (
    <div className="post-ingestion-layout">
      {/* Left Side: Predict Warnings */}
      <section className="left-section">
        <div className="section-header">
          <h2>Risk Analysis</h2>
        </div>
        <div className="section-content">
          <button 
            className="btn btn-primary btn-large"
            onClick={handlePredictWarnings}
            disabled={isPredicting}
          >
            {isPredicting ? (
              <>
                <div className="predict-spinner"></div>
                Processing...
              </>
            ) : hasReport ? (
              <>
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M10 2L3 7L10 12L17 7L10 2Z" fill="currentColor"/>
                  <path d="M3 13L10 18L17 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                View Report
              </>
            ) : (
              <>
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M10 2L12 8L18 9L12 10L10 16L8 10L2 9L8 8L10 2Z" fill="currentColor"/>
                </svg>
                Predict Warnings in Clauses in Files
              </>
            )}
          </button>
          
          {progressMessage && !hasReport && (
            <div className="progress-message">
              <div className="progress-spinner"></div>
              <span>{progressMessage}</span>
            </div>
          )}
        </div>
      </section>
      
      {/* Report Popup Modal */}
      {showReportPopup && (
        <div className="report-popup-overlay" onClick={() => setShowReportPopup(false)}>
          <div className="report-popup-content" onClick={(e) => e.stopPropagation()}>
            <div className="report-popup-header">
              <h2>Risk Audit Report</h2>
              <button 
                className="report-popup-close"
                onClick={() => setShowReportPopup(false)}
                aria-label="Close"
              >
                ×
              </button>
            </div>
            <div className="report-popup-body">
              <div className="markdown-content" dangerouslySetInnerHTML={{ __html: formatMarkdown(reportContent) }} />
            </div>
          </div>
        </div>
      )}

      {/* Right Side: Q&A Section */}
      <section className="right-section">
        <div className="section-header">
          <h2>Q&A Assistant</h2>
        </div>
        <div className="qa-container">
          <div className="qa-messages">
            {qaMessages.length === 0 && !isLoading ? (
              <div className="qa-welcome">
                <p>Ask questions about your ingested documents</p>
              </div>
            ) : (
              <>
                {qaMessages.map((msg, index) => (
                  <div key={index} className={`qa-message ${msg.sender === 'You' ? 'qa-user' : 'qa-bot'}`}>
                    <div className="qa-message-header">
                      <span className="qa-sender">{msg.sender}</span>
                      <span className="qa-time">{msg.time}</span>
                    </div>
                    <div className="qa-message-text">{msg.text}</div>
                  </div>
                ))}
                {isLoading && (
                  <div className="qa-message qa-bot">
                    <div className="qa-message-header">
                      <span className="qa-sender">DocuScout</span>
                      <span className="qa-time">{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                    <div className="qa-message-text qa-loading">
                      <div className="qa-loading-spinner"></div>
                      <span>Processing your question...</span>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
          <div className="qa-input-container">
            <textarea
              className="qa-input"
              placeholder="Ask a question about your documents..."
              rows={2}
              value={qaInput}
              onChange={(e) => setQaInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleQASend()
                }
              }}
              disabled={isLoading}
            />
            <button 
              className="btn btn-primary"
              onClick={handleQASend}
              disabled={isLoading || !qaInput.trim()}
            >
              {isLoading ? (
                'Wait'
              ) : (
                <>
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path d="M18 2L9 11M18 2L12 18L9 11M18 2L2 8L9 11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  Send
                </>
              )}
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}

