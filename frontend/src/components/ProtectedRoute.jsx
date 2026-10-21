import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/useAuth.js'
import Loader from './Loader.jsx'

export default function ProtectedRoute({ children, adminOnly = false }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <Loader />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (adminOnly && !user.is_staff) return <Navigate to="/" replace />
  return children
}