// src/components/Layout.jsx

import Header from './Header'; // 1. Import your feature-rich Header component
import './Layout.css';

const Layout = ({ children }) => {
  return (
    <div className="app-layout">
      
      {/* 2. Use the Header component here */}
      <Header />

      <main className="main-content">
        <div className="container">
          {children}
        </div>
      </main>

      <footer className="app-footer">
        <div className="container">
          <p>&copy; 2025 My Awesome Site. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Layout;