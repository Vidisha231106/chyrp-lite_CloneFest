// src/components/MathJaxRenderer.jsx

import { useEffect, useRef } from 'react';
import './MathJaxRenderer.css';

const MathJaxRenderer = ({ content }) => {
  const contentRef = useRef(null);

  useEffect(() => {
    // Load MathJax if not already loaded
    if (!window.MathJax) {
      const script = document.createElement('script');
      script.src = 'https://polyfill.io/v3/polyfill.min.js?features=es6';
      script.async = true;
      document.head.appendChild(script);

      const mathJaxScript = document.createElement('script');
      mathJaxScript.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js';
      mathJaxScript.async = true;
      document.head.appendChild(mathJaxScript);

      mathJaxScript.onload = () => {
        window.MathJax = {
          tex: {
            inlineMath: [['\\(', '\\)']],
            displayMath: [['\\[', '\\]']],
            processEscapes: true,
            processEnvironments: true
          },
          options: {
            skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
          }
        };
        renderMath();
      };
    } else {
      renderMath();
    }

    function renderMath() {
      if (contentRef.current && window.MathJax) {
        window.MathJax.typesetPromise([contentRef.current]).catch((err) => {
          console.error('MathJax rendering error:', err);
        });
      }
    }
  }, [content]);

  return (
    <div 
      ref={contentRef}
      className="mathjax-content"
      dangerouslySetInnerHTML={{ __html: content }}
    />
  );
};

export default MathJaxRenderer;
