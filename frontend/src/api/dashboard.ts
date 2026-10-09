import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const api = axios.create({ baseURL: API_BASE_URL })

// Attach JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('jwt')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// On 401, clear JWT and redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('jwt')
      window.location.href = '/'
    }
    return Promise.reject(error)
  },
)

export interface ChannelKPIs {
  subscriber_count: number
  total_views: number
  watch_time_minutes: number
  video_count: number
}

export interface DashboardOverview {
  kpis: ChannelKPIs
  snapshot_date: string
  data_source: 'cache' | 'live'
}

export interface VideoItem {
  video_id: string
  title: string
  thumbnail_url: string
  views: number
  likes: number
  comments: number
  published_at: string | null
  engagement_rate: number
}

export const getOverview = (): Promise<DashboardOverview> =>
  api.get<DashboardOverview>('/api/dashboard/overview').then((r) => r.data)

export const getTopVideos = (): Promise<VideoItem[]> =>
  api.get<VideoItem[]>('/api/dashboard/top-videos').then((r) => r.data)
