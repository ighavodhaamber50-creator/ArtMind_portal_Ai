import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import Analyze from './pages/Analyze.jsx'
import ArtworkDetail from './pages/ArtworkDetail.jsx'
import Assistant from './pages/Assistant.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Gallery from './pages/Gallery.jsx'
import Home from './pages/Home.jsx'
import Login from './pages/Login.jsx'
import NotFound from './pages/NotFound.jsx'
import Register from './pages/Register.jsx'
import Analytics from './pages/Analytics.jsx'
import MyArtworks from './pages/MyArtworks.jsx'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="gallery" element={<Gallery />} />
        <Route path="artworks/:id" element={<ArtworkDetail />} />
        <Route path="assistant" element={<Assistant />} />
        <Route path="analyze" element={<Analyze />} />
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Register />} />
        <Route
          path="collection"
          element={<ProtectedRoute><Dashboard /></ProtectedRoute>}
        />
        <Route
  path="my-artworks"
  element={<ProtectedRoute><MyArtworks /></ProtectedRoute>}
/>
        <Route path="dashboard" element={<Navigate to="/collection" replace />} />
        <Route
  path="analytics"
  element={<ProtectedRoute adminOnly><Analytics /></ProtectedRoute>}
/>
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}