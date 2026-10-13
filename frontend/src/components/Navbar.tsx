import { NavLink } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `text-sm transition-colors ${
    isActive ? 'font-medium text-clinical-primary' : 'text-clinical-textMuted hover:text-clinical-primary'
  }`;

export default function Navbar() {
  const { user, signOut } = useAuth();
  return (
    <nav className="bg-white border-b border-clinical-border sticky top-0 z-20">
      <div className="max-w-[1200px] mx-auto px-12 h-[72px] flex items-center justify-between">
        <NavLink to="/" className="flex items-center gap-2.5">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#13293D" strokeWidth="1.6">
            <path d="M9 3a4 4 0 0 0-4 4v1.2A3.5 3.5 0 0 0 3 11.5a3.5 3.5 0 0 0 1.8 3.06A3.5 3.5 0 0 0 7.5 19H9" strokeLinecap="round" />
            <path d="M15 3a4 4 0 0 1 4 4v1.2a3.5 3.5 0 0 1 2 3.3 3.5 3.5 0 0 1-1.8 3.06A3.5 3.5 0 0 1 16.5 19H15" strokeLinecap="round" />
            <path d="M9 3v18M15 3v18" strokeLinecap="round" />
          </svg>
          <span className="font-serif text-[19px] font-semibold text-clinical-primary">NeuroDetect AI</span>
        </NavLink>
        <div className="flex gap-8">
          <NavLink to="/" end className={linkClass}>Home</NavLink>
          <NavLink to="/upload" className={linkClass}>Upload</NavLink>
          <NavLink to="/history" className={linkClass}>History</NavLink>
          <NavLink to="/model" className={linkClass}>Model Info</NavLink>
          <NavLink to="/settings" className={linkClass}>Settings</NavLink>
          {user ? <button onClick={signOut} className="text-sm text-clinical-textMuted hover:text-clinical-primary">Sign out</button> : <NavLink to="/signin" className="text-sm text-clinical-primary font-medium">Sign in</NavLink>}
        </div>
      </div>
    </nav>
  );
}
