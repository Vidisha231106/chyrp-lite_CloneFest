// src/components/EnhancedContent.jsx

import { useState, useEffect } from 'react';
import apiClient from '../api';
import CodeHighlighter from './CodeHighlighter';
import MathJaxRenderer from './MathJaxRenderer';
import './EnhancedContent.css';

const EnhancedContent = ({ content }) => {
  const [processedContent, setProcessedContent] = useState(content);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (content) {
      processContent();
    }
  }, [content]);

  const processContent = async () => {
    setLoading(true);
    try {
      // First, process for MathJax
      let processed = content;
      
      // Convert MathJax syntax to HTML spans
      processed = processed.replace(/\$([^$]+)\$/g, '<span class="math-inline">\\($1\\)</span>');
      processed = processed.replace(/\$\$([^$]+)\$\$/g, '<div class="math-display">\\[$1\\]</div>');
      processed = processed.replace(/\\\[(.*?)\\\]/g, '<div class="math-display">\\[$1\\]</div>');
      processed = processed.replace(/\\\((.*?)\\\)/g, '<span class="math-inline">\\($1\\)</span>');
      
      // Process LaTeX environments
      processed = processed.replace(/\\begin\{([^}]+)\}(.*?)\\end\{\1\}/gs, 
        '<div class="math-latex">\\begin{$1}$2\\end{$1}</div>');
      
      setProcessedContent(processed);
    } catch (error) {
      console.error('Error processing content:', error);
      setProcessedContent(content);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="content-processing">Processing content...</div>;
  }

  // Check if content has code blocks
  const hasCodeBlocks = content && content.includes('```');
  
  if (hasCodeBlocks) {
    return <CodeHighlighter content={content} />;
  }

  return <MathJaxRenderer content={processedContent} />;
};

export default EnhancedContent;
