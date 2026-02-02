import { useEffect, useState } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'

interface Deal {
  id: string
  status: string
  last_error: string | null
  company_name: string | null
  founders: string[] | null
  sector: string | null
  geography: string | null
  stage: string | null
  round_size: string | null
  metrics: Record<string, string> | null
  investment_brief: string[] | null
  tags: string[] | null
  raw_text: string
  created_at: string
}

interface DealDetailProps {
  dealId: string
  onClose: () => void
}

const statusColors: Record<string, string> = {
  pending: '#ff9800',
  extracting: '#2196f3',
  validating: '#9c27b0',
  completed: '#4caf50',
  failed: '#f44336',
}

export function DealDetail({ dealId, onClose }: DealDetailProps) {
  const [deal, setDeal] = useState<Deal | null>(null)
  const [loading, setLoading] = useState(true)
  const { status: wsStatus } = useWebSocket(dealId)

  useEffect(() => {
    const fetchDeal = async () => {
      try {
        const res = await fetch(`/api/deals/${dealId}`)
        if (res.ok) {
          setDeal(await res.json())
        }
      } catch (err) {
        console.error('Failed to fetch deal:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchDeal()
  }, [dealId])

  // Refetch when WebSocket status changes
  useEffect(() => {
    if (wsStatus && deal && wsStatus !== deal.status) {
      fetch(`/api/deals/${dealId}`)
        .then((res) => res.json())
        .then(setDeal)
        .catch(console.error)
    }
  }, [wsStatus, dealId, deal])

  if (loading) {
    return <div style={styles.container}>Loading...</div>
  }

  if (!deal) {
    return <div style={styles.container}>Deal not found</div>
  }

  const currentStatus = wsStatus || deal.status

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>{deal.company_name || 'Processing...'}</h2>
        <button onClick={onClose} style={styles.closeButton}>×</button>
      </div>

      <div style={styles.statusRow}>
        <span
          style={{
            ...styles.status,
            background: statusColors[currentStatus] || '#999',
          }}
        >
          {currentStatus}
        </span>
        {deal.last_error && (
          <span style={styles.error}>Error: {deal.last_error}</span>
        )}
      </div>

      {currentStatus === 'completed' && (
        <>
          <section style={styles.section}>
            <h3 style={styles.sectionTitle}>Overview</h3>
            <div style={styles.grid}>
              {deal.sector && <Field label="Sector" value={deal.sector} />}
              {deal.geography && <Field label="Geography" value={deal.geography} />}
              {deal.stage && <Field label="Stage" value={deal.stage} />}
              {deal.round_size && <Field label="Round Size" value={deal.round_size} />}
            </div>
          </section>

          {deal.founders && deal.founders.length > 0 && (
            <section style={styles.section}>
              <h3 style={styles.sectionTitle}>Founders</h3>
              <ul style={styles.list}>
                {deal.founders.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </section>
          )}

          {deal.metrics && Object.keys(deal.metrics).length > 0 && (
            <section style={styles.section}>
              <h3 style={styles.sectionTitle}>Metrics</h3>
              <div style={styles.grid}>
                {Object.entries(deal.metrics).map(([key, value]) => (
                  <Field key={key} label={key} value={value} />
                ))}
              </div>
            </section>
          )}

          {deal.investment_brief && deal.investment_brief.length > 0 && (
            <section style={styles.section}>
              <h3 style={styles.sectionTitle}>Investment Brief</h3>
              <ul style={styles.bullets}>
                {deal.investment_brief.map((bullet, i) => (
                  <li key={i}>{bullet}</li>
                ))}
              </ul>
            </section>
          )}

          {deal.tags && deal.tags.length > 0 && (
            <section style={styles.section}>
              <h3 style={styles.sectionTitle}>Tags</h3>
              <div style={styles.tags}>
                {deal.tags.map((tag, i) => (
                  <span key={i} style={styles.tag}>{tag}</span>
                ))}
              </div>
            </section>
          )}
        </>
      )}

      <section style={styles.section}>
        <h3 style={styles.sectionTitle}>Raw Text</h3>
        <pre style={styles.rawText}>{deal.raw_text}</pre>
      </section>
    </div>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div style={styles.field}>
      <span style={styles.label}>{label}</span>
      <span style={styles.value}>{value}</span>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    background: 'white',
    padding: '24px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    maxHeight: '80vh',
    overflow: 'auto',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '16px',
  },
  title: {
    fontSize: '24px',
    margin: 0,
  },
  closeButton: {
    background: 'none',
    border: 'none',
    fontSize: '28px',
    cursor: 'pointer',
    color: '#666',
    lineHeight: 1,
  },
  statusRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '24px',
  },
  status: {
    padding: '6px 12px',
    borderRadius: '4px',
    color: 'white',
    fontSize: '14px',
    textTransform: 'uppercase',
  },
  error: {
    color: '#f44336',
    fontSize: '14px',
  },
  section: {
    marginBottom: '24px',
  },
  sectionTitle: {
    fontSize: '14px',
    textTransform: 'uppercase',
    color: '#666',
    marginBottom: '12px',
    borderBottom: '1px solid #eee',
    paddingBottom: '8px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '16px',
  },
  field: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  label: {
    fontSize: '12px',
    color: '#999',
    textTransform: 'uppercase',
  },
  value: {
    fontSize: '16px',
  },
  list: {
    listStyle: 'none',
    padding: 0,
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  bullets: {
    paddingLeft: '20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  tags: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
  },
  tag: {
    padding: '4px 12px',
    background: '#e3f2fd',
    color: '#1976d2',
    borderRadius: '16px',
    fontSize: '14px',
  },
  rawText: {
    background: '#f5f5f5',
    padding: '16px',
    borderRadius: '4px',
    fontSize: '13px',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    maxHeight: '200px',
    overflow: 'auto',
  },
}
