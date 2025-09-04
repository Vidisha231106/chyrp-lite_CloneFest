// src/pages/Post.jsx

import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import apiClient from '../api';
import './Post.css';

const Post = () => {
  const [post, setPost] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const { postId } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchPostAndUser = async () => {
      try {
        const postResponse = await apiClient.get(`/posts/${postId}`);
        setPost(postResponse.data);
        const userResponse = await apiClient.get('/users/me');
        setCurrentUser(userResponse.data);
      } catch {
        console.error("Error fetching data");
      } finally {
        setLoading(false);
      }
    };
    fetchPostAndUser();
  }, [postId]);

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this post?')) {
      try {
        await apiClient.delete(`/posts/${postId}`);
        navigate('/');
      } catch{
        alert('Failed to delete post. You may not have permission.');
      }
    }
  };

  const handleLike = async () => {
    try {
      await apiClient.post(`/posts/${postId}/like`);
      alert(`Toggled like for post ${postId}!`);
    } catch {
      alert("You must be logged in to like a post.");
    }
  };

  const handleEditClick = () => {
    // NEW: Check if post has media and show appropriate message
    const hasMedia = post.media_id !== null && post.media_id !== undefined;
    if (hasMedia) {
      const confirmMessage = "This post contains media and cannot be edited. You can only delete posts with media. Do you want to go to the edit page to remove the media first?";
      if (window.confirm(confirmMessage)) {
        navigate(`/edit-post/${post.id}`);
      }
    } else {
      navigate(`/edit-post/${post.id}`);
    }
  };

  if (loading) return <p>Loading...</p>;
  if (!post) return <h1>Post not found</h1>;

  const canEdit = currentUser && (
    currentUser.group.permissions.includes('edit_post') ||
    (currentUser.id === post.owner.id && currentUser.group.permissions.includes('edit_own_post'))
  );

  const canDelete = currentUser && (
    currentUser.group.permissions.includes('delete_post') ||
    (currentUser.id === post.owner.id && currentUser.group.permissions.includes('delete_own_post'))
  );

  // NEW: Check if post has media
  const hasMedia = post.media_id !== null && post.media_id !== undefined;

  // --- A helper function to render the main content ---
  const renderPostContent = () => {
    // Priority 1: Modern Media Post (checks for the 'media' object)
    if (post.media) {
      const mediaUrl = `http://127.0.0.1:8000/media/${post.media.id}`;
      if (post.media_type === 'image') {
        return <img src={mediaUrl} alt={post.title || post.clean} style={{ maxWidth: '100%', height: 'auto' }} />;
      }
      if (post.media_type === 'audio') {
        return <audio controls src={mediaUrl} style={{ width: '100%' }} />;
      }
      if (post.media_type === 'video') {
        return <video controls src={mediaUrl} style={{ maxWidth: '100%', height: 'auto' }} />;
      }
    }

    // Priority 2: Legacy Filesystem Photo Post
    if (post.feather === 'photo' && post.body?.startsWith('/uploads/')) {
      return <img src={`http://127.0.0.1:8000${post.body}`} alt={post.title || post.clean} style={{ maxWidth: '100%', height: 'auto' }} />;
    }
    
    // Priority 3: Formatted Text Posts (Quote, Link)
    if (post.feather === 'quote') {
        return <blockquote style={{ borderLeft: '4px solid #007bff', paddingLeft: '20px', margin: '20px 0', fontStyle: 'italic', fontSize: '1.2em' }}><ReactMarkdown>{post.body || ''}</ReactMarkdown></blockquote>;
    }
      
    if (post.feather === 'link') {
        return <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '20px', margin: '20px 0' }}><ReactMarkdown>{post.body || ''}</ReactMarkdown></div>;
    }

    // Fallback: Default text post
    return <ReactMarkdown>{post.body || ''}</ReactMarkdown>;
  };

  return (
    <div className="post-page">
      <header className="post-header">
        <Link to="/" className="back-link">← Back to Home</Link>
        <h1>{post.title || post.clean}</h1>
        <div className="post-meta">
          <span>By {post.owner.login}</span>
          <span>{new Date(post.created_at).toLocaleDateString()}</span>
          {canEdit && (
            <button 
              onClick={handleEditClick} 
              className={`btn-edit ${hasMedia ? 'btn-edit-restricted' : ''}`}
              title={hasMedia ? 'This post has media and cannot be edited directly' : 'Edit this post'}
            >
              {hasMedia ? 'Edit (Restricted)' : 'Edit'}
            </button>
          )}
          {canDelete && <button onClick={handleDelete} className="btn-delete">Delete</button>}
        </div>
      </header>
      
      {/* NEW: Show info message for media posts */}
      {hasMedia && canEdit && (
        <div className="media-post-info" style={{ 
          backgroundColor: '#e7f3ff', 
          border: '1px solid #b6d7ff', 
          padding: '10px', 
          borderRadius: '4px', 
          marginBottom: '20px',
          fontSize: '0.9em',
          color: '#0056b3'
        }}>
          <strong>Note:</strong> This post contains media and cannot be edited. You can only delete it or remove the media first to make it editable.
        </div>
      )}
      
      <div className="post-content">
        {renderPostContent()}
      </div>
      <footer className="post-footer">
        <button onClick={handleLike} className="btn-like">❤️ Like</button>
      </footer>
    </div>
  );
};

export default Post;