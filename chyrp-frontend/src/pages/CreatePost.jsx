// src/pages/CreatePost.jsx

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api';
import MultiFileUploader from '../components/MultiFileUploader';
import './CreatePost.css';

const CreatePost = () => {
  const [title, setTitle] = useState('');
  const [clean, setClean] = useState(''); // URL Slug
  const [body, setBody] = useState('');
  const [isPage, setIsPage] = useState(false);
  const [feather, setFeather] = useState('text'); // 'text' | 'photo' | 'quote' | 'link' | 'video' | 'audio'
  const [photoFile, setPhotoFile] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [audioFile, setAudioFile] = useState(null);
  const [quote, setQuote] = useState('');
  const [attribution, setAttribution] = useState('');
  const [url, setUrl] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState('draft'); // 'draft' or 'public'
  const [error, setError] = useState('');
  const navigate = useNavigate();
  
  // --- NEW: State for AI processing ---
  const [isEnhancing, setIsEnhancing] = useState(false);

  // --- NEW: Handler for the AI button ---
  const handleEnhanceWithAI = async () => {
    if (!body.trim()) {
      setError("Please write some text before enhancing with AI.");
      return;
    }
    setError('');
    setIsEnhancing(true);
    try {
      const response = await apiClient.post('/ai/enhance', { text: body });
      setBody(response.data.enhanced_text); // Update the textarea with AI content
    } catch (err) {
      const detail = err?.response?.data?.detail || "Failed to enhance text. Please try again.";
      setError(`AI Error: ${detail}`);
    } finally {
      setIsEnhancing(false);
    }
  };


  const handleUploadComplete = (uploadedUrls) => {
    console.log('Files uploaded successfully:', uploadedUrls);
    // You can add logic here to handle the uploaded URLs
    // For example, add them to the post body or show them in a preview
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      if (feather === 'photo') {
        if (!photoFile) {
          setError('Please choose an image to upload.');
          return;
        }
        const form = new FormData();
        form.append('clean', clean);
        form.append('title', title);
        form.append('status', status);
        form.append('file', photoFile);
        await apiClient.post('/posts/photo', form, { headers: { 'Content-Type': 'multipart/form-data' } });
      } else if (feather === 'quote') {
        if (!quote.trim() || !attribution.trim()) {
          setError('Please enter both quote and attribution.');
          return;
        }
        const form = new FormData();
        form.append('clean', clean);
        form.append('quote', quote);
        form.append('attribution', attribution);
        form.append('status', status);
        await apiClient.post('/posts/quote', form, { headers: { 'Content-Type': 'multipart/form-data' } });
      } else if (feather === 'link') {
        if (!title.trim() || !url.trim()) {
          setError('Please enter both title and URL.');
          return;
        }
        const form = new FormData();
        form.append('clean', clean);
        form.append('title', title);
        form.append('url', url);
        form.append('description', description);
        form.append('status', status);
        await apiClient.post('/posts/link', form, { headers: { 'Content-Type': 'multipart/form-data' } });
      } else if (feather === 'video') {
        if (!videoFile) {
          setError('Please choose a video file to upload.');
          return;
        }
        const form = new FormData();
        form.append('clean', clean);
        form.append('title', title);
        form.append('status', status);
        form.append('file', videoFile);
        await apiClient.post('/posts/video', form, { headers: { 'Content-Type': 'multipart/form-data' } });
      } else if (feather === 'audio') {
        if (!audioFile) {
          setError('Please choose an audio file to upload.');
          return;
        }
        const form = new FormData();
        form.append('clean', clean);
        form.append('title', title);
        form.append('status', status);
        form.append('file', audioFile);
        await apiClient.post('/posts/audio', form, { headers: { 'Content-Type': 'multipart/form-data' } });
      } else {
        const postData = {
          content_type: isPage ? 'page' : 'post',
          title,
          body,
          clean,
          status,
          feather: 'text',
        };
        await apiClient.post('/posts/', postData);
      }
      navigate('/');
    } catch (err) {
      let detail = err?.response?.data?.detail;
      if (!detail && typeof err?.response?.data === 'object') {
        try { detail = JSON.stringify(err.response.data); } catch {
          if (!photoFile) {
            setError('Please choose an image to upload.');
            return;
          }
        }
      }
      setError(detail ? `Failed: ${detail}` : 'Failed to create post. Please try again.');
    }
  };

  return (
    <div className="create-post-container">
      <h1>Create New {isPage ? 'Page' : 'Post'}</h1>

      <div className="content-type-toggle">
        <label>
          <input type="checkbox" checked={isPage} onChange={(e) => setIsPage(e.target.checked)} />
          Create as a static page
        </label>
      </div>

      {error && <p className="error-message">{error}</p>}

      <form onSubmit={handleSubmit}>
        {/* Feather Type Selection */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '20px' }}>
          <strong>Post Type:</strong>
          <label>
            <input type="radio" name="feather" value="text" checked={feather === 'text'} onChange={() => setFeather('text')} /> Text
          </label>
          <label>
            <input type="radio" name="feather" value="photo" checked={feather === 'photo'} onChange={() => setFeather('photo')} /> Photo
          </label>
          <label>
            <input type="radio" name="feather" value="quote" checked={feather === 'quote'} onChange={() => setFeather('quote')} /> Quote
          </label>
          <label>
            <input type="radio" name="feather" value="link" checked={feather === 'link'} onChange={() => setFeather('link')} /> Link
          </label>
          <label>
            <input type="radio" name="feather" value="video" checked={feather === 'video'} onChange={() => setFeather('video')} /> Video
          </label>
          <label>
            <input type="radio" name="feather" value="audio" checked={feather === 'audio'} onChange={() => setFeather('audio')} /> Audio
          </label>
        </div>

        {/* Title field - hide for quote posts */}
        {feather !== 'quote' && (
          <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" required />
        )}

        {/* URL Slug - always required */}
        <input type="text" value={clean} onChange={(e) => setClean(e.target.value)} placeholder="URL Slug (e.g., my-new-post)" required />

        {/* Dynamic content based on feather type */}
        {feather === 'text' ? (
          // --- NEW: Added a wrapper and AI button ---
          <div className="editor-wrapper">
            <textarea value={body} onChange={(e) => setBody(e.target.value)} placeholder="Write your content..." rows="15" required />
            <button 
              type="button" 
              className="ai-enhance-btn" 
              onClick={handleEnhanceWithAI} 
              disabled={isEnhancing}
            >
              {isEnhancing ? 'Enhancing...' : '✨ Enhance with AI'}
            </button>
          </div>
        ) : feather === 'photo' ? (
          <div>
            <label>Choose image to upload:</label>
            <input type="file" accept="image/*" onChange={(e) => setPhotoFile(e.target.files?.[0] || null)} required />
          </div>
        ) : feather === 'video' ? (
          <div>
            <label>Choose video file to upload:</label>
            <input type="file" accept="video/*" onChange={(e) => setVideoFile(e.target.files?.[0] || null)} required />
          </div>
        ) : feather === 'audio' ? (
          <div>
            <label>Choose audio file to upload:</label>
            <input type="file" accept="audio/*" onChange={(e) => setAudioFile(e.target.files?.[0] || null)} required />
          </div>
        ) : feather === 'quote' ? (
          <div>
            <textarea value={quote} onChange={(e) => setQuote(e.target.value)} placeholder="Enter the quote..." rows="8" required />
            <input type="text" value={attribution} onChange={(e) => setAttribution(e.target.value)} placeholder="Attribution (e.g., Albert Einstein)" required />
          </div>
        ) : (
          <div>
            <input type="url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com" required />
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional description..." rows="4" />
          </div>
        )}

        <div className="form-actions">
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="draft">Save as Draft</option>
            <option value="public">Publish/</option>
          </select>
          <button type="submit">Submit</button>
        </div>
      </form>
      
      {/* Multi-File Uploader Section */}
      <div style={{ marginTop: '40px', padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
        <MultiFileUploader onUploadComplete={handleUploadComplete} />
      </div>
    </div>
  );
};

export default CreatePost;