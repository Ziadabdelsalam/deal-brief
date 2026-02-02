import { useState } from 'react'
import { DealForm } from './components/DealForm'
import { DealList } from './components/DealList'
import { DealDetail } from './components/DealDetail'

function App() {
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  const handleDealSubmitted = (dealId: string) => {
    setSelectedDealId(dealId)
    setRefreshTrigger((t) => t + 1)
  }

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <h1 style={styles.title}>Deal Brief</h1>
        <p style={styles.subtitle}>LLM-powered deal extraction pipeline</p>
      </header>

      <main style={styles.main}>
        <div style={styles.sidebar}>
          <DealForm onSubmit={handleDealSubmitted} />
          <DealList
            onSelect={setSelectedDealId}
            refreshTrigger={refreshTrigger}
          />
        </div>

        <div style={styles.content}>
          {selectedDealId ? (
            <DealDetail
              dealId={selectedDealId}
              onClose={() => setSelectedDealId(null)}
            />
          ) : (
            <div style={styles.placeholder}>
              <p>Select a deal to view details or submit a new one</p>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  app: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
  },
  header: {
    background: '#1976d2',
    color: 'white',
    padding: '24px 32px',
  },
  title: {
    margin: 0,
    fontSize: '28px',
  },
  subtitle: {
    margin: '4px 0 0',
    opacity: 0.9,
    fontSize: '14px',
  },
  main: {
    flex: 1,
    display: 'grid',
    gridTemplateColumns: '400px 1fr',
    gap: '24px',
    padding: '24px 32px',
    maxWidth: '1400px',
    margin: '0 auto',
    width: '100%',
  },
  sidebar: {
    display: 'flex',
    flexDirection: 'column',
    gap: '24px',
  },
  content: {
    minHeight: '400px',
  },
  placeholder: {
    background: 'white',
    padding: '48px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    textAlign: 'center',
    color: '#666',
  },
}

export default App
