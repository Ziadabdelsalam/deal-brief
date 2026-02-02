import { useEffect, useState } from 'react'

interface Deal {
  id: string
  status: string
  company_name: string | null
  sector: string | null
  stage: string | null
  created_at: string
}

interface DealListProps {
  onSelect: (dealId: string) => void
  refreshTrigger: number
}

const statusColors: Record<string, string> = {
  pending: '#ff9800',
  extracting: '#2196f3',
  validating: '#9c27b0',
  completed: '#4caf50',
  failed: '#f44336',
}

export function DealList({ onSelect, refreshTrigger }: DealListProps) {
  const [deals, setDeals] = useState<Deal[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDeals = async () => {
      try {
        const res = await fetch('/api/deals')
        const data = await res.json()
        setDeals(data.deals)
      } catch (err) {
        console.error('Failed to fetch deals:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchDeals()
    const interval = setInterval(fetchDeals, 5000)
    return () => clearInterval(interval)
  }, [refreshTrigger])

  if (loading) {
    return <p>Loading deals...</p>
  }

  if (deals.length === 0) {
    return <p style={styles.empty}>No deals yet. Submit one above.</p>
  }

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Recent Deals</h2>
      <div style={styles.list}>
        {deals.map((deal) => (
          <div
            key={deal.id}
            onClick={() => onSelect(deal.id)}
            style={styles.item}
          >
            <div style={styles.header}>
              <span style={styles.company}>
                {deal.company_name || 'Processing...'}
              </span>
              <span
                style={{
                  ...styles.status,
                  background: statusColors[deal.status] || '#999',
                }}
              >
                {deal.status}
              </span>
            </div>
            <div style={styles.meta}>
              {deal.sector && <span>{deal.sector}</span>}
              {deal.stage && <span> • {deal.stage}</span>}
            </div>
            <div style={styles.date}>
              {new Date(deal.created_at).toLocaleDateString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    background: 'white',
    padding: '24px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  title: {
    marginBottom: '16px',
    fontSize: '18px',
  },
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  item: {
    padding: '16px',
    border: '1px solid #eee',
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'background 0.2s',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  company: {
    fontWeight: 600,
    fontSize: '16px',
  },
  status: {
    padding: '4px 8px',
    borderRadius: '4px',
    color: 'white',
    fontSize: '12px',
    textTransform: 'uppercase',
  },
  meta: {
    color: '#666',
    fontSize: '14px',
  },
  date: {
    color: '#999',
    fontSize: '12px',
    marginTop: '8px',
  },
  empty: {
    color: '#666',
    textAlign: 'center',
    padding: '24px',
  },
}
