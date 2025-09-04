// src/pages/Home.jsx

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api';
import './Home.css';

const Home = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // This function fetches posts from the backend when the component loads
  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const response = await apiClient.get('/posts/?content_type=post');
        setPosts(response.data);
      } catch (error) {
        console.error("Failed to fetch posts:", error);
        setError('Could not load posts. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    fetchPosts();
  }, []); // The empty array ensures this runs only once

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
  if (error) {
    return <div className="container"><p style={{ color: 'red' }}>{error}</p></div>;
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
            {posts.length > 0 ? (
              posts.map(post => (
                <article key={post.id} className="post-card">
                  <div className="post-content">
                    <h3 className="post-title">
                      <Link to={`/posts/${post.id}`}>{post.title || post.clean}</Link>
                    </h3>
                    {/* Enhanced content display for different post types */}
                    {post.feather === 'photo' ? (
                      <Link to={`/posts/${post.id}`}>
                        <img
                          src={post.body}
                          alt={post.title || post.clean}
                          style={{
                            width: '100%',
                            height: '220px',
                            objectFit: 'cover',
                            borderRadius: '8px'
                          }}
                        />
                      </Link>
                    ) : post.feather === 'link' ? (
                      <div style={{
                        border: '1px solid #ddd',
                        borderRadius: '6px',
                        padding: '12px',
                        margin: '10px 0',
                        backgroundColor: '#f9f9f9',
                        fontSize: '0.9em'
                      }}>
                        <strong>🔗 Link Post</strong><br />
                        {(() => {
                          // Extract URL from the post body
                          const urlMatch = post.body?.match(/https?:\/\/[^\s]+/);
                          const url = urlMatch ? urlMatch[0] : null;
                          return url ? (
                            <a href={url} target="_blank" rel="noopener noreferrer" style={{
                              color: '#007bff',
                              textDecoration: 'underline',
                              fontWeight: 'bold'
                            }}>
                              {post.title || 'Shared Link'} 🔗
                            </a>
                          ) : (
                            post.title || 'Shared Link'
                          );
                        })()}
                      </div>
                    ) : (
                      <p className="post-excerpt">
                        {post.body ? `${post.body.substring(0, 150)}...` : 'This is a feather post.'}
                      </p>
                    )}
                    <div className="post-meta">
                      <span className="post-author">By {post.owner.login}</span>
                      <span className="post-date">{formatDate(post.created_at)}</span>
                      {/* --- Likes display --- */}
                      <span className="like-display">❤️ {post.likes_count}</span>
                    </div>
                    <Link to={`/posts/${post.id}`} className="read-more">
                      Read More →
                    </Link>
                  </div>
                </article>
              ))
            ) : (
              <p>No posts have been published yet.</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
};

export default Home;