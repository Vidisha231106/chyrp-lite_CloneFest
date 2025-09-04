// src/pages/EditPost.jsx

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import apiClient from '../api';
import './CreatePost.css'; // Re-using styles from CreatePost

const EditPost = () => {
  const { postId } = useParams();
  const navigate = useNavigate();

  // --- STATE MANAGEMENT ---
  const [post, setPost] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    clean: '',
    body: '',
    status: 'draft',
    feather: 'text'
  });
  const [newMediaFile, setNewMediaFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isMediaPost, setIsMediaPost] = useState(false);

  // 1. Fetch the full post data
  useEffect(() => {
    apiClient.get(`/posts/${postId}`)
      .then(response => {
        const postData = response.data;
        setPost(postData);
        
        // Check if this post has media (cannot be edited)
        const hasMedia = postData.media_id !== null && postData.media_id !== undefined;
        setIsMediaPost(hasMedia);
        
        setFormData({
          title: postData.title || '',
          clean: postData.clean || '',
          body: postData.body || '',
          status: postData.status || 'draft',
          feather: postData.feather || 'text'
        });
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch post:", err);
        setError("Failed to load post data.");
        setLoading(false);
      });
  }, [postId]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e) => {
    setNewMediaFile(e.target.files?.[0] || null);
  };
  
  const handleRemoveMedia = async () => {
    // UPDATED: More specific confirmation message
    const isLegacy = post.feather === 'photo' && !post.media;
    const confirmMessage = isLegacy 
      ? "Are you sure you want to convert this photo post to a text post? The image will be removed."
      : "Are you sure you want to remove this post's media? This cannot be undone.";

    if (!window.confirm(confirmMessage)) {
      return;
    }

    try {
      if (post.media) {
          const response = await apiClient.delete(`/posts/${postId}/media`);
          setPost(response.data); 
          setIsMediaPost(false); // Post can now be edited
          alert("Media removed successfully!");
      } else {
          const updatedFormData = { ...formData, body: '', feather: 'text' };
          await apiClient.put(`/posts/${postId}`, updatedFormData);
          setFormData(updatedFormData);
          setPost(prev => ({ ...prev, body: '', feather: 'text', media: null }));
          setIsMediaPost(false); // Post can now be edited
          alert("Post successfully converted to a text post.");
      }
    } catch (err) {
      alert("Failed to remove media.");
      console.error(err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // NEW: Check if this is a media post and show appropriate message
    if (isMediaPost) {
      setError('Posts with media cannot be edited. Please remove the media first or delete the post.');
      return;
    }

    let updatedPostData = { ...formData };

    try {
      if (newMediaFile) {
        const mediaForm = new FormData();
        mediaForm.append('file', newMediaFile);
        
        await apiClient.put(`/posts/${postId}/media`, mediaForm, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        if (post.feather === 'photo' && !post.media) {
            updatedPostData.body = `Image: ${newMediaFile.name}`;
        }
        
        // After adding media, this becomes a media post that can't be edited
        setIsMediaPost(true);
      }

      await apiClient.put(`/posts/${postId}`, {
        title: updatedPostData.title,
        clean: updatedPostData.clean,
        body: updatedPostData.body,
        status: updatedPostData.status
      });

      alert("Post updated successfully!");
      navigate(`/posts/${postId}`);
    } catch (err) {
      // NEW: Handle the 403 error specifically
      if (err?.response?.status === 403 && err?.response?.data?.detail?.includes('Posts with media cannot be edited')) {
        setError('This post has media attached and cannot be edited. You can only delete posts with media or remove the media first.');
      } else {
        const detail = err?.response?.data?.detail || "An unexpected error occurred.";
        setError(`Failed to update post: ${detail}`);
      }
    }
  };

  const handleCancel = () => {
    navigate(-1);
  };

  if (loading) return <p>Loading editor...</p>;
  if (!post) return <h1>Post not found</h1>;

  const isLegacyPhotoPost = post.feather === 'photo' && post.body?.startsWith('/uploads/');

  return (
    <div className="create-post-container">
      <h1>Edit Post: {post.title || post.clean}</h1>
      
      {/* NEW: Show warning for media posts */}
      {isMediaPost && (
        <div className="warning-message" style={{ 
          backgroundColor: '#fff3cd', 
          border: '1px solid #ffeaa7', 
          padding: '15px', 
          borderRadius: '4px', 
          marginBottom: '20px',
          color: '#856404'
        }}>
          <strong>Note:</strong> This post contains media and cannot be edited. You can only delete the post or remove the media to make it editable.
        </div>
      )}
      
      {error && <p className="error-message">{error}</p>}

      {(post.media || isLegacyPhotoPost) && (
        <div className="media-management-section">
          <h3>Current Media</h3>
          {post.media?.media_type === 'image' && <img src={`http://127.0.0.1:8000/media/${post.media.id}`} alt="Current media" />}
          {isLegacyPhotoPost && <img src={`http://127.0.0.1:8000${post.body}`} alt="Current media" />}
          {post.media?.media_type === 'audio' && <audio controls src={`http://127.0.0.1:8000/media/${post.media.id}`} />}
          {post.media?.media_type === 'video' && <video controls src={`http://127.0.0.1:8000/media/${post.media.id}`} />}
          
          <div className="media-actions">
            {/* UPDATED: Button text is now conditional */}
            <button type="button" onClick={handleRemoveMedia} className="btn-delete">
              {isLegacyPhotoPost ? 'Convert to Text Post' : 'Remove Media'}
            </button>
            <div>
              <label htmlFor="media-replace">Replace Media:</label>
              <input id="media-replace" type="file" onChange={handleFileChange} />
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <input 
          name="title" 
          type="text" 
          value={formData.title} 
          onChange={handleChange} 
          placeholder="Title" 
          required 
          disabled={isMediaPost}
        />
        <input 
          name="clean" 
          type="text" 
          value={formData.clean} 
          onChange={handleChange} 
          placeholder="URL Slug" 
          required 
          disabled={isMediaPost}
        />
        
        {isLegacyPhotoPost || ['photo', 'audio', 'video'].includes(post.feather) ? (
          <p><em>Post body is auto-generated for this media type. You can replace the media above.</em></p>
        ) : (
          <textarea 
            name="body" 
            value={formData.body} 
            onChange={handleChange} 
            placeholder="Write your content..." 
            rows="15" 
            disabled={isMediaPost}
          />
        )}
        
        <div className="form-actions">
          <select 
            name="status" 
            value={formData.status} 
            onChange={handleChange}
            disabled={isMediaPost}
          >
            <option value="draft">Save as Draft</option>
            <option value="public">Publish</option>
            <option value="private">Private</option>
          </select>
          <div>
            <button type="button" onClick={handleCancel} className="btn-cancel">Cancel</button>
            <button 
              type="submit" 
              disabled={isMediaPost}
              style={isMediaPost ? { opacity: 0.5, cursor: 'not-allowed' } : {}}
            >
              Save Changes
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};

export default EditPost;