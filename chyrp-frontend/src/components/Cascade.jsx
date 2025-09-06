// src/components/Cascade.jsx

import { useState, useEffect, useRef, useCallback } from 'react';
import apiClient from '../api';
import './Cascade.css';

const Cascade = ({ 
  endpoint = '/cascade/posts', 
  limit = 10, 
  renderItem, 
  className = '',
  onLoadMore,
  initialParams = {}
}) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [cursor, setCursor] = useState(null);
  const [error, setError] = useState(null);
  
  const observerRef = useRef();
  const loadingRef = useRef();

  const loadItems = useCallback(async (reset = false) => {
    if (loading) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const params = {
        limit,
        ...initialParams,
        ...(cursor && !reset ? { cursor } : {})
      };
      
      const response = await apiClient.get(endpoint, { params });
      const newItems = response.data.posts || []; // Use 'posts' and fallback to an empty array
      const newCursor = response.data.next_cursor;
      
      if (reset) {
        setItems(newItems);
      } else {
        setItems(prev => [...prev, ...newItems]);
      }
      
      setCursor(newCursor);
      setHasMore(!!newCursor);
      
      if (onLoadMore) {
        onLoadMore(newItems, reset);
      }
    } catch (error) {
      console.error('Failed to load items:', error);
      setError('Failed to load more items');
    } finally {
      setLoading(false);
    }
  }, [endpoint, limit, cursor, loading, initialParams, onLoadMore]);

  const lastItemRef = useCallback((node) => {
    if (loading) return;
    if (observerRef.current) observerRef.current.disconnect();
    
    observerRef.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting && hasMore) {
        loadItems();
      }
    });
    
    if (node) observerRef.current.observe(node);
  }, [loading, hasMore, loadItems]);

  useEffect(() => {
    loadItems(true);
  }, [endpoint, limit, JSON.stringify(initialParams)]);

  useEffect(() => {
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, []);

  const retry = () => {
    setError(null);
    loadItems();
  };

  if (items.length === 0 && !loading) {
    return (
      <div className={`cascade-container ${className}`}>
        <div className="cascade-empty">
          <p>No items found.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`cascade-container ${className}`}>
      {items.map((item, index) => {
        const isLastItem = index === items.length - 1;
        return (
          <div
            key={item.id || index}
            ref={isLastItem ? lastItemRef : null}
            className="cascade-item"
          >
            {renderItem ? renderItem(item, index) : (
              <div className="cascade-item-default">
                <pre>{JSON.stringify(item, null, 2)}</pre>
              </div>
            )}
          </div>
        );
      })}
      
      {loading && (
        <div ref={loadingRef} className="cascade-loading">
          <div className="cascade-spinner"></div>
          <span>Loading more...</span>
        </div>
      )}
      
      {error && (
        <div className="cascade-error">
          <p>{error}</p>
          <button onClick={retry} className="cascade-retry-btn">
            Try Again
          </button>
        </div>
      )}
      
      {!hasMore && items.length > 0 && (
        <div className="cascade-end">
          <p>You've reached the end!</p>
        </div>
      )}
    </div>
  );
};

export default Cascade;
