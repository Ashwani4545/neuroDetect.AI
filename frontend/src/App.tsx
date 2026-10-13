import { Navigate, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Landing from './pages/Landing';
import Upload from './pages/Upload';
import Analysis from './pages/Analysis';
import History from './pages/History';
import ModelInfo from './pages/ModelInfo';
import Settings from './pages/Settings';
import Auth from './pages/Auth';
import { useAuth } from './auth/AuthContext';

export default function App() {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-12 text-center text-clinical-textMuted">Loading secure session…</div>;
  return (
    <div className="min-h-full flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/signin" element={user ? <Navigate to="/upload" replace /> : <Auth mode="signin" />} />
          <Route path="/signup" element={user ? <Navigate to="/upload" replace /> : <Auth mode="signup" />} />
          <Route path="/auth/callback" element={<Auth mode="signin" />} />
          <Route path="/upload" element={user ? <Upload /> : <Navigate to="/signin" replace />} />
          <Route path="/analysis/:id" element={user ? <Analysis /> : <Navigate to="/signin" replace />} />
          <Route path="/history" element={user ? <History /> : <Navigate to="/signin" replace />} />
          <Route path="/model" element={<ModelInfo />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Landing />} />
        </Routes>
      </main>
      <footer className="text-center text-xs text-clinical-textMuted py-4 border-t border-clinical-border">
        NeuroDetect AI — research / decision-support prototype. Not a diagnostic device.
      </footer>
    </div>
  );
}
