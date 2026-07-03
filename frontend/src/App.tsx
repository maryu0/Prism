import { useEffect, useState } from 'react'

type HealthResponse = {
  status: string
  checks: Record<string, string>
}

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const apiUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
    fetch(`${apiUrl}/health`)
      .then((res) => res.json())
      .then(setHealth)
      .catch((err) => setError(String(err)))
  }, [])

  return (
    <main className="min-h-screen bg-white p-8 font-mono text-sm text-neutral-800">
      <h1 className="mb-4 text-lg font-semibold">Prism — Phase 0 scaffold</h1>
      {error && <p className="text-red-600">Could not reach backend: {error}</p>}
      {!error && !health && <p>Checking backend health…</p>}
      {health && (
        <div>
          <p className="mb-2">
            Overall: <strong>{health.status}</strong>
          </p>
          <ul className="list-inside list-disc">
            {Object.entries(health.checks).map(([service, status]) => (
              <li key={service}>
                {service}: {status}
              </li>
            ))}
          </ul>
        </div>
      )}
    </main>
  )
}

export default App
