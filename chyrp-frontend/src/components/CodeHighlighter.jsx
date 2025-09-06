// src/components/CodeHighlighter.jsx

import { useState, useEffect } from 'react';
import apiClient from '../api';
import './CodeHighlighter.css';

const CodeHighlighter = ({ content }) => {
  const [highlightedContent, setHighlightedContent] = useState(content);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (content && content.includes('```')) {
      processCodeBlocks();
    } else {
      setHighlightedContent(content);
    }
  }, [content]);

  const processCodeBlocks = async () => {
    setLoading(true);
    try {
      // Extract code blocks from content
      const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
      let processedContent = content;
      let match;
      let blockIndex = 0;

      while ((match = codeBlockRegex.exec(content)) !== null) {
        const [fullMatch, language, code] = match;
        const blockId = `code-block-${blockIndex++}`;
        
        try {
          // Call the highlighter API
          const response = await apiClient.post('/highlighter/highlight', null, {
            params: {
              code: code.trim(),
              language: language || 'text'
            }
          });
          
          const highlightedCode = response.data.code;
          const highlightedBlock = `
            <div class="code-block" data-language="${language || 'text'}">
              <div class="code-header">
                <span class="code-language">${language || 'text'}</span>
                <button class="copy-button" onclick="copyToClipboard('${blockId}')">Copy</button>
              </div>
              <pre class="code-content" id="${blockId}"><code>${highlightedCode}</code></pre>
            </div>
          `;
          
          processedContent = processedContent.replace(fullMatch, highlightedBlock);
        } catch (error) {
          console.error('Failed to highlight code block:', error);
          // Fallback to plain code block
          const fallbackBlock = `
            <div class="code-block" data-language="${language || 'text'}">
              <div class="code-header">
                <span class="code-language">${language || 'text'}</span>
                <button class="copy-button" onclick="copyToClipboard('${blockId}')">Copy</button>
              </div>
              <pre class="code-content" id="${blockId}"><code>${code.trim()}</code></pre>
            </div>
          `;
          processedContent = processedContent.replace(fullMatch, fallbackBlock);
        }
      }

      setHighlightedContent(processedContent);
    } catch (error) {
      console.error('Error processing code blocks:', error);
      setHighlightedContent(content);
    } finally {
      setLoading(false);
    }
  };

  // Add copy to clipboard function to window
  useEffect(() => {
    window.copyToClipboard = (elementId) => {
      const element = document.getElementById(elementId);
      if (element) {
        const text = element.textContent;
        navigator.clipboard.writeText(text).then(() => {
          // Show feedback
          const button = element.parentElement.querySelector('.copy-button');
          const originalText = button.textContent;
          button.textContent = 'Copied!';
          setTimeout(() => {
            button.textContent = originalText;
          }, 2000);
        }).catch(err => {
          console.error('Failed to copy text: ', err);
        });
      }
    };
  }, []);

  if (loading) {
    return <div className="code-processing">Processing code blocks...</div>;
  }

  return (
    <div 
      className="highlighted-content"
      dangerouslySetInnerHTML={{ __html: highlightedContent }}
    />
  );
};

export default CodeHighlighter;
