import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

interface UserProfile {
  id: string
  email: string
  name: string
  google_id: string
}

export function useAuth() {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()

  const logout = useCallback(() => {
    localStorage.removeItem('jwt')
    setUser(null)
    navigate('/', { replace: true })
  }, [navigate])

  useEffect(() => {
    const token = localStorage.getItem('jwt')
    if (!token) {
      setIsLoading(false)
      return
    }

    axios
      .get<UserProfile>(`${API_BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((res) => setUser(res.data))
      .catch(() => {
        localStorage.removeItem('jwt')
      })
      .finally(() => setIsLoading(false))
  }, [])

  return { user, isLoading, logout }
}
