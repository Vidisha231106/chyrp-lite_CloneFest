// src/pages/CreatePost.jsx

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api';

const CreatePost = () => {
  const [title, setTitle] = useState('');
  const [clean, setClean] = useState('');
  const [body, setBody] = useState('');
  const [isPage, setIsPage] = useState(false);
  const [status, setStatus] = useState('draft');
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


  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const postData = {
      content_type: isPage ? 'page' : 'post',
      title,
      body,
      clean,
      status,
    };

    try {
      await apiClient.post('/posts/', postData);
      navigate('/');
    } catch (err) {
      setError('Failed to create post. Please try again.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8 bg-gradient-to-r from-purple-400 to-purple-600 bg-clip-text text-transparent">
        Create New {isPage ? 'Page' : 'Post'}
      </h1>
      
      <div className="flex items-center gap-2 mb-6">
        <label className="flex items-center gap-2 text-gray-300 cursor-pointer">
          <input 
            type="checkbox" 
            checked={isPage} 
            onChange={(e) => setIsPage(e.target.checked)}
            className="rounded bg-slate-800 border-purple-500/20 text-purple-500 focus:ring-purple-500/20" 
          />
          Create as a static page
        </label>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

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
          
          <button type="submit" className="btn">
            Submit
          </button>
        </div>
      
    </div>
  );
};

export default CreatePost;