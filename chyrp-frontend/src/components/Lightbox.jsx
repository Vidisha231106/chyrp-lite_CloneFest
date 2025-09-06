// src/components/Lightbox.jsx

import { useState, useEffect } from 'react';
import apiClient from '../api';
import './Lightbox.css';

const Lightbox = ({ images, postId, isOpen, onClose }) => {
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [imageData, setImageData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && postId) {
      fetchPostImages();
    }
  }, [isOpen, postId]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!isOpen) return;
      
      switch (e.key) {
        case 'Escape':
          onClose();
          break;
        case 'ArrowLeft':
          goToPrevious();
          break;
        case 'ArrowRight':
          goToNext();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, currentImageIndex]);

  const fetchPostImages = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get(`/lightbox/post/${postId}/images`);
      setImageData(response.data);
    } catch (error) {
      console.error('Failed to fetch images:', error);
      setImageData(images || []);
    } finally {
      setLoading(false);
    }
  };

  const goToPrevious = () => {
    setCurrentImageIndex((prev) => 
      prev === 0 ? imageData.length - 1 : prev - 1
    );
  };

  const goToNext = () => {
    setCurrentImageIndex((prev) => 
      prev === imageData.length - 1 ? 0 : prev + 1
    );
  };

  const handleImageClick = (index) => {
    setCurrentImageIndex(index);
  };

  if (!isOpen || imageData.length === 0) return null;

  const currentImage = imageData[currentImageIndex];

  return (
    <div className="lightbox-overlay" onClick={onClose}>
      <div className="lightbox-container" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="lightbox-header">
          <div className="lightbox-counter">
            {currentImageIndex + 1} of {imageData.length}
          </div>
          <button className="lightbox-close" onClick={onClose}>
            ×
          </button>
        </div>

        {/* Main Image */}
        <div className="lightbox-main">
          <button 
            className="lightbox-nav lightbox-prev" 
            onClick={goToPrevious}
            disabled={imageData.length <= 1}
          >
            ‹
          </button>
          
          <div className="lightbox-image-container">
            {loading ? (
              <div className="lightbox-loading">Loading...</div>
            ) : (
              <img
                src={currentImage.url}
                alt={currentImage.alt || `Image ${currentImageIndex + 1}`}
                className="lightbox-image"
                onLoad={() => setLoading(false)}
              />
            )}
          </div>
          
          <button 
            className="lightbox-nav lightbox-next" 
            onClick={goToNext}
            disabled={imageData.length <= 1}
          >
            ›
          </button>
        </div>

        {/* Thumbnails */}
        {imageData.length > 1 && (
          <div className="lightbox-thumbnails">
            {imageData.map((image, index) => (
              <img
                key={index}
                src={image.thumbnail || image.url}
                alt={image.alt || `Thumbnail ${index + 1}`}
                className={`lightbox-thumbnail ${
                  index === currentImageIndex ? 'active' : ''
                }`}
                onClick={() => handleImageClick(index)}
              />
            ))}
          </div>
        )}

        {/* Image Info */}
        {currentImage.caption && (
          <div className="lightbox-caption">
            {currentImage.caption}
          </div>
        )}
      </div>
    </div>
  );
};

export default Lightbox;
