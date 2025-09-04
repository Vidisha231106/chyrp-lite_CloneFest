// src/pages/Home.jsx

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api';
import PropTypes from 'prop-types';
import './Home.css';

const PostPreviewContent = ({ post }) => {
  // Priority 1: Modern Media Post (checks for the 'media' object)
  if (post.media && post.media_type === 'image') {
    return (
      <Link to={`/posts/${post.id}`}>
        <img
          src={`http://127.0.0.1:8000/media/${post.media.id}`}
          alt={post.title || post.clean}
          className="post-card-image"
        />
      </Link>
    );
  }
  
  if (post.media && post.media_type === 'audio') {
    return (
      <div className="post-excerpt-audio">
        <strong>🎵 Audio Post</strong><br/>
        {post.title || 'Audio Content'}
      </div>
    );
  }
  
  if (post.media && post.media_type === 'video') {
    return (
      <div className="post-excerpt-video">
        <strong>🎬 Video Post</strong><br/>
        {post.title || 'Video Content'}
      </div>
    );
  }
  
  // Priority 2: Legacy Filesystem Photo Post
  if (post.feather === 'photo' && post.body?.startsWith('/uploads/')) {
    return (
      <Link to={`/posts/${post.id}`}>
        <img
          src={`http://127.0.0.1:8000${post.body}`}
          alt={post.title || post.clean}
          className="post-card-image"
        />
      </Link>
    );
  }

  // Priority 3: Formatted Text Posts (Quote, Link)
  if (post.feather === 'quote') {
    return (
      <div className="post-excerpt-quote">
        <strong>💬 Quote</strong><br/>
        {post.body ? `${post.body.substring(0, 100)}...` : 'Quote content'}
      </div>
    );
  }

  if (post.feather === 'link') {
    return (
      <div className="post-excerpt-link">
        <strong>🔗 Link Post</strong><br/>
        {post.title || 'Shared Link'}
      </div>
    );
  }

  // Fallback: Default text post
  return (
    <p className="post-excerpt">
      {post.body ? `${post.body.substring(0, 150)}...` : 'This post has no text content.'}
    </p>
  );
};

PostPreviewContent.propTypes = {
  post: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string,
    clean: PropTypes.string.isRequired,
    body: PropTypes.string,
    feather: PropTypes.string,
    media: PropTypes.shape({
      id: PropTypes.number.isRequired,
    }),
    media_type: PropTypes.string,
    media_id: PropTypes.number, // NEW: Added media_id for better detection
    owner: PropTypes.shape({
        login: PropTypes.string.isRequired,
    }).isRequired,
    created_at: PropTypes.string.isRequired,
  }).isRequired,
};

const Home = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const response = await apiClient.get('/posts/?content_type=post');
        setPosts(response.data);
      } catch (error) {
        console.error("Failed to fetch posts:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchPosts();
  }, []);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return <div className="container"><p>Loading posts...</p></div>;
  }

  return (
    <div className="home">
      <div className="container">
        <section className="hero">
          <h1>Welcome to My Awesome Site</h1>
          <p className="hero-subtitle">
            Discover insights, tutorials, and stories from the world of technology and development.
          </p>
        </section>

        <section className="latest-posts">
          <h2>Latest Posts</h2>
          <div className="posts-grid">
            {posts.map(post => {
              // NEW: Determine if post has media for styling purposes
              const hasMedia = post.media_id !== null && post.media_id !== undefined;
              
              return (
                <article key={post.id} className={`post-card ${hasMedia ? 'post-card-media' : 'post-card-text'}`}>
                  <div className="post-content">
                    <h3 className="post-title">
                      <Link to={`/posts/${post.id}`}>
                        {post.title || post.clean}
                        {hasMedia && <span className="media-indicator" title="This post contains media">📎</span>}
                      </Link>
                    </h3>
                    
                    <PostPreviewContent post={post} />

                    <div className="post-meta">
                      <span className="post-author">By {post.owner.login}</span>
                      <span className="post-date">{formatDate(post.created_at)}</span>
                    </div>
                    <Link to={`/posts/${post.id}`} className="read-more">
                      Read More →
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
          
          {posts.length === 0 && (
            <p style={{ textAlign: 'center', color: '#666', marginTop: '40px' }}>
              No posts found. <Link to="/create-post">Create your first post!</Link>
            </p>
          )}
        </section>
      </div>
    </div>
  );
};

export default Home;