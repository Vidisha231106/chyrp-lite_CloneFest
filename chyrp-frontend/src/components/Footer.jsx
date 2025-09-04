// src/components/Footer.jsx
const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-t border-purple-200/20 dark:border-purple-800/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-12">
          <div className="md:col-span-1">
            <h4 className="text-2xl lg:text-3xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 dark:from-purple-400 dark:to-indigo-400 bg-clip-text text-transparent mb-4">
              My Awesome Site
            </h4>
            <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
              A modern blog sharing insights, stories, and ideas with the world.
              Where creativity meets technology.
            </p>
          </div>
          
          <div>
            <h5 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Links</h5>
            <ul className="space-y-2">
              <li>
                <a 
                  href="/" 
                  className="text-gray-600 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors duration-200 flex items-center group"
                >
                  <span className="w-2 h-2 bg-purple-600 dark:bg-purple-400 rounded-full mr-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200"></span>
                  Blog
                </a>
              </li>
              <li>
                <a 
                  href="/about" 
                  className="text-gray-600 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors duration-200 flex items-center group"
                >
                  <span className="w-2 h-2 bg-purple-600 dark:bg-purple-400 rounded-full mr-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200"></span>
                  About
                </a>
              </li>
              <li>
                <a 
                  href="/contact" 
                  className="text-gray-600 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors duration-200 flex items-center group"
                >
                  <span className="w-2 h-2 bg-purple-600 dark:bg-purple-400 rounded-full mr-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200"></span>
                  Contact
                </a>
              </li>
            </ul>
          </div>
          
          <div>
            <h5 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Connect</h5>
            <ul className="space-y-2">
              <li>
                <a 
                  href="#" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-gray-600 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors duration-200 flex items-center group"
                >
                  <span className="w-2 h-2 bg-purple-600 dark:bg-purple-400 rounded-full mr-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200"></span>
                  Twitter
                </a>
              </li>
              <li>
                <a 
                  href="#" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-gray-600 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors duration-200 flex items-center group"
                >
                  <span className="w-2 h-2 bg-purple-600 dark:bg-purple-400 rounded-full mr-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200"></span>
                  LinkedIn
                </a>
              </li>
              <li>
                <a 
                  href="#" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-gray-600 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors duration-200 flex items-center group"
                >
                  <span className="w-2 h-2 bg-purple-600 dark:bg-purple-400 rounded-full mr-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200"></span>
                  GitHub
                </a>
              </li>
            </ul>
          </div>
        </div>
        
        <div className="mt-12 pt-8 border-t border-purple-200/30 dark:border-purple-800/30 text-center">
          <p className="text-gray-600 dark:text-gray-400">
            &copy; {currentYear} My Awesome Site. All rights reserved.
            <span className="block sm:inline sm:ml-2 mt-1 sm:mt-0 text-purple-600 dark:text-purple-400">
              Built with 💜 and React
            </span>
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;