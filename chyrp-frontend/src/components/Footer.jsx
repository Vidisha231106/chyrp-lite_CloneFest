import './Footer.css';

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-content">
          <div className="footer-section">
            <h4>My Awesome Site</h4>
            <p className="text-muted">
              A modern blog sharing insights, stories, and ideas with the world.
            </p>
          </div>
          
          <div className="footer-section">
            <h5>Quick Links</h5>
            <ul className="footer-links">
              <li><a href="/">Blog</a></li>
              <li><a href="/about">About</a></li>
              <li><a href="/contact">Contact</a></li>
            </ul>
          </div>
          
          <div className="footer-section">
            <h5>Connect</h5>
            <ul className="footer-links">
              <li><a href="#" target="_blank" rel="noopener noreferrer">Twitter</a></li>
              <li><a href="#" target="_blank" rel="noopener noreferrer">LinkedIn</a></li>
              <li><a href="#" target="_blank" rel="noopener noreferrer">GitHub</a></li>
            </ul>
          </div>
        </div>
        
        <div className="footer-bottom">
          <p>&copy; {currentYear} My Awesome Site. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
