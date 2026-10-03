import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Landing from './pages/Landing';
import Upload from './pages/Upload';
import Analysis from './pages/Analysis';
import History from './pages/History';
import ModelInfo from './pages/ModelInfo';
import Settings from './pages/Settings';

export default function App() {
  return (
    <div className="min-h-full flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/analysis/:id" element={<Analysis />} />
          <Route path="/history" element={<History />} />
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
