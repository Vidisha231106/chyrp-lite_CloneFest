import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Header.css';

const Header = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      isScrolled ? 'bg-slate-900/95 backdrop-blur-md shadow-lg shadow-purple-900/10' : 'bg-transparent'
    }`}>
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link 
            to="/" 
            className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-purple-600 
                       bg-clip-text text-transparent hover:from-purple-500 hover:to-purple-700 
                       transition-all duration-300"
          >
            ChyrpLite
          </Link>
          
          <div className="hidden md:flex items-center gap-8">
            <Link to="/" className={`nav-link ${location.pathname === '/' ? 'text-purple-400 after:w-full' : ''}`}>
              Home
            </Link>
            <Link to="/about" className={`nav-link ${location.pathname === '/about' ? 'text-purple-400 after:w-full' : ''}`}>
              About
            </Link>
            <Link to="/contact" className={`nav-link ${location.pathname === '/contact' ? 'text-purple-400 after:w-full' : ''}`}>
              Contact
            </Link>
            {user ? (
              <>
                <Link to="/create-post" className="btn btn-secondary">
                  Create Post
                </Link>
                <button 
                  onClick={handleLogout}
                  className="text-gray-300 hover:text-purple-400 transition-colors"
                >
                  Logout
                </button>
              </>
            ) : (
              <Link to="/login" className="btn">
                Login
              </Link>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button className="md:hidden p-2 rounded-lg hover:bg-purple-500/10">
            <svg className="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
      </nav>
    </header>
  );
};

export default Header;