// src/components/EmbedPreview.jsx

import { useState, useEffect } from 'react';
import apiClient from '../api';
import './EmbedPreview.css';

const EmbedPreview = ({ url, content }) => {
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (url || content) {
      fetchEmbedPreview();
    }
  }, [url, content]);

  const fetchEmbedPreview = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.post('/embed/preview', null, {
        params: {
          url: url,
          content: content
        }
      });
      
      setPreview(response.data);
    } catch (error) {
      console.error('Failed to fetch embed preview:', error);
      setError('Failed to load embed preview');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="embed-preview embed-loading">
        <div className="embed-loading-spinner"></div>
        <span>Loading preview...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="embed-preview embed-error">
        <div className="embed-error-icon">⚠️</div>
        <span>{error}</span>
      </div>
    );
  }

  if (!preview) {
    return null;
  }

  return (
    <div className="embed-preview">
      <div className="embed-card">
        {preview.image && (
          <div className="embed-image">
            <img src={preview.image} alt={preview.title || 'Preview'} />
          </div>
        )}
        
        <div className="embed-content">
          <div className="embed-header">
            {preview.favicon && (
              <img src={preview.favicon} alt="" className="embed-favicon" />
            )}
            <span className="embed-site-name">{preview.site_name}</span>
          </div>
          
          <h3 className="embed-title">
            <a href={preview.url} target="_blank" rel="noopener noreferrer">
              {preview.title}
            </a>
          </h3>
          
          {preview.description && (
            <p className="embed-description">{preview.description}</p>
          )}
          
          <div className="embed-footer">
            <span className="embed-url">{preview.url}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmbedPreview;
