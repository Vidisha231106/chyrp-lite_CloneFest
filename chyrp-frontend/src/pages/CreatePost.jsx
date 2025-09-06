// src/pages/CreatePost.jsx

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../api';
import './CreatePost.css';

const CreatePost = () => {
  // --- STATE MANAGEMENT ---
  const [title, setTitle] = useState('');
  const [clean, setClean] = useState('');
  const [isPage, setIsPage] = useState(false);
  const [feather, setFeather] = useState('text'); // The state for Post Type
  const [status, setStatus] = useState('draft');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // State for different post content
  const [body, setBody] = useState(''); // For text posts
  const [file, setFile] = useState(null); // For photo, video, audio
  const [quote, setQuote] = useState('');
  const [attribution, setAttribution] = useState('');
  const [url, setUrl] = useState('');
  const [description, setDescription] = useState('');

  // State for tags and categories
  const [allCategories, setAllCategories] = useState([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState('');
  const [tagsInput, setTagsInput] = useState('');

  // --- DATA FETCHING ---
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await apiClient.get('/categories');
        setAllCategories(response.data);
        if (response.data.length > 0) {
          setSelectedCategoryId(response.data[0].id);
        }
      } catch (err) {
        console.error("Failed to fetch categories", err);
      }
    };
    fetchCategories();
  }, []);

  // --- HANDLERS ---
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      // For post types that involve file uploads (photo, video, audio)
      if (['photo', 'video', 'audio'].includes(feather)) {
        if (!file) { setError(`Please choose a ${feather} file.`); return; }
        const form = new FormData();
        form.append('clean', clean);
        form.append('title', title);
        form.append('status', status);
        form.append('category_ids', JSON.stringify([parseInt(selectedCategoryId)]));
        form.append('tags', JSON.stringify(tagsInput.split(',').map(tag => tag.trim()).filter(Boolean)));
        form.append('file', file);
        await apiClient.post(`/posts/${feather}`, form, { headers: { 'Content-Type': 'multipart/form-data' } });
      }
      // For post types that use form data but no files (quote, link)
      else if (['quote', 'link'].includes(feather)) {
        const form = new FormData();
        form.append('clean', clean);
        form.append('status', status);
        form.append('category_ids', JSON.stringify([parseInt(selectedCategoryId)]));
        form.append('tags', JSON.stringify(tagsInput.split(',').map(tag => tag.trim()).filter(Boolean)));
        if (feather === 'quote') {
            form.append('quote', quote);
            form.append('attribution', attribution);
        } else { // link
            form.append('title', title);
            form.append('url', url);
            form.append('description', description);
        }
        await apiClient.post(`/posts/${feather}`, form, { headers: { 'Content-Type': 'multipart/form-data' } });
      }
      // For standard text posts
      else {
        const postData = {
          content_type: isPage ? 'page' : 'post',
          title, body, clean, status,
          feather: 'text',
          tags: tagsInput.split(',').map(tag => tag.trim()).filter(Boolean),
          category_ids: [parseInt(selectedCategoryId)],
        };
        await apiClient.post('/posts/', postData);
      }
      
      navigate('/');
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to create post.');
    }
  };

  // --- RENDER ---
  return (
    <div className="create-post-container">
      <h1>Create New {isPage ? 'Page' : 'Post'}</h1>
      {error && <p className="error-message">{error}</p>}
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <strong>Post Type:</strong>
          <div className="feather-radios">
            <label><input type="radio" name="feather" value="text" checked={feather === 'text'} onChange={() => setFeather('text')} /> Text</label>
            <label><input type="radio" name="feather" value="photo" checked={feather === 'photo'} onChange={() => setFeather('photo')} /> Photo</label>
            <label><input type="radio" name="feather" value="quote" checked={feather === 'quote'} onChange={() => setFeather('quote')} /> Quote</label>
            <label><input type="radio" name="feather" value="link" checked={feather === 'link'} onChange={() => setFeather('link')} /> Link</label>
            <label><input type="radio" name="feather" value="video" checked={feather === 'video'} onChange={() => setFeather('video')} /> Video</label>
            <label><input type="radio" name="feather" value="audio" checked={feather === 'audio'} onChange={() => setFeather('audio')} /> Audio</label>
          </div>
        </div>

        {feather !== 'quote' && <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Title" required />}
        <input type="text" value={clean} onChange={(e) => setClean(e.target.value)} placeholder="URL Slug (e.g., my-new-post)" required />

        {/* Conditional inputs for each feather type */}
        {feather === 'text' && <textarea value={body} onChange={(e) => setBody(e.target.value)} placeholder="Write your content..." rows={15} />}
        {feather === 'photo' && <input type="file" accept="image/*" onChange={(e) => setFile(e.target.files[0])} />}
        {feather === 'video' && <input type="file" accept="video/*" onChange={(e) => setFile(e.target.files[0])} />}
        {feather === 'audio' && <input type="file" accept="audio/*" onChange={(e) => setFile(e.target.files[0])} />}
        {feather === 'quote' && (
            <>
                <textarea value={quote} onChange={(e) => setQuote(e.target.value)} placeholder="Quote text..." rows={5} />
                <input type="text" value={attribution} onChange={(e) => setAttribution(e.target.value)} placeholder="Attribution" />
            </>
        )}
        {feather === 'link' && (
            <>
                <input type="url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com" />
                <textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional description..." rows={3} />
            </>
        )}

        <div className="taxonomy-selectors">
          <div className="form-group">
            <label htmlFor="category">Category</label>
            <select id="category" value={selectedCategoryId} onChange={(e) => setSelectedCategoryId(e.target.value)}>
              {allCategories.map(category => (
                <option key={category.id} value={category.id}>{category.name}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="tags">Tags (comma-separated)</label>
            <input type="text" id="tags" value={tagsInput} onChange={(e) => setTagsInput(e.target.value)} placeholder="e.g., python, react, cooking" />
          </div>
        </div>

        <div className="form-actions">
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="draft">Save as Draft</option>
            <option value="public">Publish</option>
          </select>
          <button type="submit">Submit</button>
        </div>
      </form>
    </div>
  );
};

export default CreatePost;