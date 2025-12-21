'use client'

import { useState } from 'react'
import { apiClient } from '@/lib/api'

interface PostIngestionPageProps {
  sessionId: string | null
}

export default function PostIngestionPage({ sessionId }: PostIngestionPageProps) {
  const [qaMessages, setQaMessages] = useState<Array<{ sender: string; text: string; time: string }>>([])
  const [qaInput, setQaInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

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

  const handlePredictWarnings = () => {
    // TODO: Implement predict warnings functionality
    alert('Predict Warnings functionality will be implemented in the next phase.')
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
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 2L12 8L18 9L12 10L10 16L8 10L2 9L8 8L10 2Z" fill="currentColor"/>
            </svg>
            Predict Warnings in Clauses in Files
          </button>
        </div>
      </section>

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

