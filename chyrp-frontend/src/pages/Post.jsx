// src/pages/Post.jsx

import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import apiClient from '../api';
import Comments from '../components/Comments';
import EnhancedContent from '../components/EnhancedContent';
import Lightbox from '../components/Lightbox';
import EmbedPreview from '../components/EmbedPreview';
import './Post.css';

const Post = () => {
  const [post, setPost] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const { postId } = useParams();
  const navigate = useNavigate();

  // src/pages/Post.jsx

  useEffect(() => {
    const fetchPostAndUser = async () => {
      try {
        // --- Step 1: Fetch the post data ---
        const postResponse = await apiClient.get(`/posts/${postId}`);
        setPost(postResponse.data);

        // --- Step 2 (NEW): Record the view ---
        // This is a "fire-and-forget" call; we don't need the response.
        // A separate try/catch ensures that if this fails, the post still loads.
        try {
          apiClient.post(`/views/posts/${postId}`);
        } catch (viewError) {
          console.error("Failed to record view:", viewError);
        }

        // --- Step 3: Fetch the current user ---
        const userResponse = await apiClient.get('/users/me');
        setCurrentUser(userResponse.data);
      } catch (error) {
        if (error.response?.status !== 401) {
          console.error("Error fetching data:", error);
        }
      } finally {
        setLoading(false);
      }
    };
    fetchPostAndUser();
  }, [postId]);

  
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
        {/* --- UPDATED META SECTION --- */}
        <div className="post-card-meta">
          <span>By {post.owner.login}</span>
          <span>{new Date(post.created_at).toLocaleDateString()}</span>
          <span className="post-card-stats">
            ❤️ {post.likes_count}
            <span style={{ marginLeft: '10px' }}>💬 {post.comments_count}</span>
          </span>
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
      <div className="post-content">
        {post.feather === 'photo' ? (
          <img
            src={post.body}
            alt={post.title || post.clean}
            style={{ maxWidth: '100%', height: 'auto', cursor: 'pointer' }}
            onClick={() => setLightboxOpen(true)}
            className="post-image"
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
        ) : post.feather === 'video' ? (
          <div className="video-container" style={{
            border: '1px solid #ddd',
            borderRadius: '8px',
            padding: '20px',
            margin: '20px 0',
            backgroundColor: '#f9f9f9'
          }}>
            <video
              controls
              style={{
                width: '100%',
                maxWidth: '800px',
                height: 'auto',
                borderRadius: '4px'
              }}
            >
              <source src={post.body} type="video/mp4" />
              <source src={post.body} type="video/webm" />
              <source src={post.body} type="video/ogg" />
              Your browser does not support the video tag.
            </video>
            {post.title && <p style={{ marginTop: '10px', fontStyle: 'italic' }}>{post.title}</p>}
          </div>
        ) : post.feather === 'audio' ? (
          <div className="audio-container" style={{
            border: '1px solid #ddd',
            borderRadius: '8px',
            padding: '20px',
            margin: '20px 0',
            backgroundColor: '#f9f9f9'
          }}>
            <audio
              controls
              style={{
                width: '100%',
                maxWidth: '600px'
              }}
            >
              <source src={post.body} type="audio/mpeg" />
              <source src={post.body} type="audio/wav" />
              <source src={post.body} type="audio/ogg" />
              Your browser does not support the audio tag.
            </audio>
            {post.title && <p style={{ marginTop: '10px', fontStyle: 'italic' }}>{post.title}</p>}
          </div>
        ) : post.feather === 'link' ? (
          <div>
            <EmbedPreview url={post.body} content={post.body} />
            {post.title && (
              <div style={{
                marginTop: '1rem',
                padding: '1rem',
                backgroundColor: '#f8f9fa',
                borderRadius: '8px',
                border: '1px solid #e9ecef'
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
                  {post.title}
                </ReactMarkdown>
              </div>
            )}
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

      {/* Comments Section */}
      <Comments postId={post.id} currentUser={currentUser} />

      {/* Lightbox */}
      <Lightbox
        isOpen={lightboxOpen}
        onClose={() => setLightboxOpen(false)}
        postId={post.id}
        images={post.feather === 'photo' ? [{ url: post.body, alt: post.title || post.clean }] : []}
      />
    </div>
  );
};

export default Post;