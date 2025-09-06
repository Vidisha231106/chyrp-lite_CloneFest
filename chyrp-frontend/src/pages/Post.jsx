// src/pages/Post.jsx

import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import ReactMarkdown from 'react-markdown';
import apiClient from '../api';
import Comments from '../components/Comments';
import EnhancedContent from '../components/EnhancedContent';
import Lightbox from '../components/Lightbox';
import EmbedPreview from '../components/EmbedPreview';
import './Post.css';

const Post = () => {
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [error, setError] = useState('');
  const { id } = useParams();
  const navigate = useNavigate();

  // src/pages/Post.jsx
  const { user } = useAuth();

  useEffect(() => {
    const fetchPost = async () => {
      try {
        const postResponse = await apiClient.get(`/posts/${postId}`);
        setPost(postResponse.data);

        // This will fail gracefully if the user is not logged in
        const userResponse = await apiClient.get('/users/me');
        setCurrentUser(userResponse.data);
      } catch (error) {
        // If getting the user fails, we still have the post data
        if (error.response?.status !== 401) {
          console.error("Error fetching data:", error);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchPost();
  }, [id]);

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this post?')) {
      try {
        await apiClient.delete(`/posts/${postId}`);
        navigate('/');
      } catch {
        alert('Failed to delete post. You may not have permission.');
      }
    }
  };

  const handleLike = async () => {
    if (!currentUser) {
      alert("You must be logged in to like a post.");
      return;
    }
    try {
      const response = await apiClient.post(`/posts/${postId}/like`);
      setPost(response.data);
    } catch (error) {
      alert("Failed to update like status. You may not have permission.");
      console.error(error);
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

  const isLikedByCurrentUser = post.liked_by_users.some(
    (user) => user.id === currentUser?.id
  );

  return (
    <div className="post-page">
      <header className="post-header">
        <Link to="/" className="back-link">← Back to Home</Link>
        <h1>{post.title || post.clean}</h1>
        <div className="post-meta">
          <span>By {post.owner.login}</span>
          {/* --- THIS IS THE CORRECTED LINE --- */}
          <span>{new Date(post.created_at).toLocaleDateString()}</span>
          {canEdit && <Link to={`/edit-post/${post.id}`} className="btn-edit">Edit</Link>}
          {canDelete && <button onClick={handleDelete} className="btn-delete">Delete</button>}
        </div>
        
        {/* Tags and Categories */}
        {(post.tags && post.tags.length > 0) || (post.categories && post.categories.length > 0) ? (
          <div className="post-taxonomy">
            {post.tags && post.tags.length > 0 && (
              <div className="post-tags">
                <span className="taxonomy-label">Tags:</span>
                {post.tags.map(tag => (
                  <span key={tag.id} className="tag" style={{ backgroundColor: tag.color }}>
                    {tag.name}
                  </span>
                ))}
              </div>
            )}
            {post.categories && post.categories.length > 0 && (
              <div className="post-categories">
                <span className="taxonomy-label">Categories:</span>
                {post.categories.map(category => (
                  <span key={category.id} className="category" style={{ backgroundColor: category.color }}>
                    {category.name}
                  </span>
                ))}
              </div>
            )}
          </div>
        ) : null}
      </header>

      {/* Post content */}
      <div className="post-content prose prose-invert max-w-none">
        {post.feather === 'photo' && post.body?.startsWith('/uploads/') ? (
          <img
            src={`http://127.0.0.1:8000${post.body}`}
            alt={post.title || post.clean}
            style={{ maxWidth: '100%', height: 'auto' }}
          />
        ) : post.feather === 'quote' ? (
          <blockquote className="border-l-4 border-primary-500 pl-4 italic text-lg text-gray-300">
            <ReactMarkdown>{post.body || ''}</ReactMarkdown>
          </blockquote>
        ) : post.feather === 'link' ? (
          <div style={{
            border: '1px solid #ddd',
            borderRadius: '8px',
            padding: '20px',
            margin: '20px 0',
            backgroundColor: '#f9f9f9'
          }}>
            <ReactMarkdown
              components={{
                a: ({ href, children }) => (
                  <a href={href} target="_blank" rel="noopener noreferrer" style={{
                    color: '#007bff',
                    textDecoration: 'underline',
                    fontWeight: 'bold'
                  }}>
                    {children} 🔗
                  </a>
                )
              }}
            >
              {post.body || ''}
            </ReactMarkdown>
          </div>
        ) : (
          <EnhancedContent content={post.body || ''} />
        )}
      </div>
      <footer className="post-footer">
        <button 
          onClick={handleLike} 
          className={`btn-like ${isLikedByCurrentUser ? 'liked' : ''}`}
          disabled={!currentUser}
        >
          ❤️ {isLikedByCurrentUser ? 'Liked' : 'Like'}
        </button>
        <span className="like-count">
          {post.likes_count} {post.likes_count === 1 ? 'like' : 'likes'}
        </span>
      </footer>
    </div>
  );
};

export default Post;
