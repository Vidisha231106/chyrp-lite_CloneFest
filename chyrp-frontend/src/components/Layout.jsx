// src/components/Layout.jsx

import { useEffect } from 'react';
import Header from './Header';
import './Layout.css'; // We'll create this file next for styling

function Layout({ children }) {
  useEffect(() => {
    // Enable smooth scrolling
    document.documentElement.style.scrollBehavior = 'smooth';
    // Set dark mode by default
    document.documentElement.classList.add('dark');
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-dark-bg to-dark-card text-gray-100 antialiased">
      <Header />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pt-20">
        <main className="prose prose-invert prose-purple max-w-none">
          {children}
        </main>
      </div>
    </div>
  );
}

export default Layout;