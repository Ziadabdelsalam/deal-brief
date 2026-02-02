import { useState } from 'react'

interface DealFormProps {
  onSubmit: (dealId: string) => void
}

export function DealForm({ onSubmit }: DealFormProps) {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!text.trim()) return

    setLoading(true)
    setError(null)

    try {
      const res = await fetch('/api/deals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: text }),
      })

      if (res.status === 409) {
        const data = await res.json()
        setError(`Duplicate deal. Existing ID: ${data.detail.existing_id}`)
        return
      }

      if (res.status === 413) {
        setError('Text too large. Maximum 10KB (~2,500 words)')
        return
      }

      if (!res.ok) {
        throw new Error('Failed to submit deal')
      }

      const deal = await res.json()
      setText('')
      onSubmit(deal.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <h2 style={styles.title}>Submit Deal</h2>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste deal text here (pitch email, memo, etc.)..."
        style={styles.textarea}
        disabled={loading}
      />
      {error && <p style={styles.error}>{error}</p>}
      <button type="submit" disabled={loading || !text.trim()} style={styles.button}>
        {loading ? 'Submitting...' : 'Extract Deal'}
      </button>
    </form>
  )
}

const styles: Record<string, React.CSSProperties> = {
  form: {
    background: 'white',
    padding: '24px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  title: {
    marginBottom: '16px',
    fontSize: '18px',
  },
  textarea: {
    width: '100%',
    height: '200px',
    padding: '12px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
    resize: 'vertical',
    fontFamily: 'inherit',
  },
  error: {
    color: '#e53935',
    marginTop: '8px',
    fontSize: '14px',
  },
  button: {
    marginTop: '16px',
    padding: '12px 24px',
    background: '#1976d2',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    cursor: 'pointer',
  },
}
