import axios, { type AxiosInstance } from 'axios'
import { useAuthStore } from './authStore'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const api: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  withCredentials: true,
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let refreshPromise: Promise<string> | null = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        if (!refreshPromise) {
          refreshPromise = axios
            .post(
              `${API_URL}/api/v1/auth/refresh`,
              {},
              { withCredentials: true },
            )
            .then((res) => {
              const token = res.data.accessToken as string
              useAuthStore.getState().setAccessToken(token)
              return token
            })
            .finally(() => {
              refreshPromise = null
            })
        }
        const token = await refreshPromise
        originalRequest.headers.Authorization = `Bearer ${token}`
        return api(originalRequest)
      } catch {
        useAuthStore.getState().clear()
      }
    }
    return Promise.reject(error)
  },
)
