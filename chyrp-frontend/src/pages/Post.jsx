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
    fetchPostAndUser();
  }, [postId]);

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
      </header>
      <div className="post-content">
        {post.feather === 'photo' ? (
          <img
            src={post.body}
            alt={post.title || post.clean}
            style={{ maxWidth: '100%', height: 'auto' }}
          />
        ) : post.feather === 'quote' ? (
          <blockquote style={{
            borderLeft: '4px solid #007bff',
            paddingLeft: '20px',
            margin: '20px 0',
            fontStyle: 'italic',
            fontSize: '1.2em',
            lineHeight: '1.6',
            color: '#333'
          }}>
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
          <ReactMarkdown>{post.body || ''}</ReactMarkdown>
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