import { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

export default function CallbackPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  useEffect(() => {
    const token = searchParams.get('token')
    if (token) {
      localStorage.setItem('jwt', token)
      navigate('/dashboard', { replace: true })
    } else {
      navigate('/', { replace: true })
    }
  }, [navigate, searchParams])

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <p className="text-white text-lg">Signing you in…</p>
    </div>
  )
}
