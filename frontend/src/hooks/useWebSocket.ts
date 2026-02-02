import { useEffect, useRef, useCallback, useState } from 'react'

interface WebSocketMessage {
  type: string
  deal_id: string
  status: string
  error?: string
}

export function useWebSocket(dealId: string | null) {
  const [status, setStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  const connect = useCallback(() => {
    if (!dealId) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/deals/${dealId}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data)
      setStatus(message.status)
      if (message.error) {
        setError(message.error)
      }
    }

    ws.onerror = () => {
      setError('WebSocket connection error')
    }

    ws.onclose = () => {
      wsRef.current = null
    }

    return () => {
      ws.close()
    }
  }, [dealId])

  useEffect(() => {
    const cleanup = connect()
    return cleanup
  }, [connect])

  return { status, error }
}
