// src/components/MultiFileUploader.jsx

import { useState } from 'react';
import apiClient from '../api';

const MultiFileUploader = ({ onUploadComplete }) => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(selectedFiles);
    setError('');
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setError('Please select files to upload.');
      return;
    }

    setUploading(true);
    setError('');

    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });

      const response = await apiClient.post('/uploads/multi', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (onUploadComplete) {
        onUploadComplete(response.data.urls);
      }
      
      setFiles([]);
      // Clear the file input
      const fileInput = document.querySelector('input[type="file"]');
      if (fileInput) fileInput.value = '';
      
    } catch (err) {
      setError(err?.response?.data?.detail || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="multi-file-uploader">
      <h3>Multi-File Uploader</h3>
      
      <div className="file-input-section">
        <label>
          Choose multiple files:
          <input 
            type="file" 
            multiple 
            onChange={handleFileChange}
            disabled={uploading}
          />
        </label>
      </div>

      {files.length > 0 && (
        <div className="selected-files">
          <h4>Selected Files ({files.length}):</h4>
          <ul>
            {files.map((file, index) => (
              <li key={index}>
                {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
              </li>
            ))}
          </ul>
        </div>
      )}

      {error && <p className="error-message">{error}</p>}

      <button 
        onClick={handleUpload} 
        disabled={uploading || files.length === 0}
        className="upload-btn"
      >
        {uploading ? 'Uploading...' : `Upload ${files.length} Files`}
      </button>
    </div>
  );
};

export default MultiFileUploader;

