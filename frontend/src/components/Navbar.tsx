import { NavLink } from 'react-router-dom';

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `px-3 py-2 text-sm font-medium rounded-md transition-colors ${
    isActive ? 'bg-clinical-primary text-white' : 'text-clinical-text hover:bg-gray-100'
  }`;

export default function Navbar() {
  return (
    <nav className="bg-white border-b border-clinical-border sticky top-0 z-20">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        <NavLink to="/" className="flex items-center gap-2 font-semibold text-clinical-primary">
          <span className="text-lg">🧠</span>
          <span>NeuroDetect AI</span>
        </NavLink>
        <div className="flex gap-1">
          <NavLink to="/" end className={linkClass}>Home</NavLink>
          <NavLink to="/upload" className={linkClass}>Upload</NavLink>
          <NavLink to="/history" className={linkClass}>History</NavLink>
          <NavLink to="/model" className={linkClass}>Model Info</NavLink>
          <NavLink to="/settings" className={linkClass}>Settings</NavLink>
        </div>
      </div>
    </nav>
  );
}
