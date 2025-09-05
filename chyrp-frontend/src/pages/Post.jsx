// src/pages/Post.jsx

import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import ReactMarkdown from 'react-markdown';
import apiClient from '../api';
import './Post.css';

const Post = () => {
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    const fetchPost = async () => {
      try {
        const response = await apiClient.get(`/posts/${id}`);
        setPost(response.data);
      } catch (err) {
        console.error('Failed to fetch post:', err);
        setError('Could not load post. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchPost();
  }, [id]);

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this post?')) {
      try {
        await apiClient.delete(`/posts/${id}`);
        navigate('/');
      } catch (err) {
        console.error('Failed to delete post:', err);
        alert('Failed to delete post. You may not have permission.');
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container text-red-400 text-center mt-12">
        {error}
      </div>
    );
  }

  if (!post) {
    return (
      <div className="container text-center mt-12">
        <h1 className="text-2xl text-gray-300">Post not found</h1>
      </div>
    );
  }

  return (
    <div className="post-page max-w-3xl mx-auto px-4 py-12 text-gray-200">
      <header className="post-header mb-8">
        <Link to="/" className="back-link text-primary-400 hover:underline">
          ← Back to Home
        </Link>
        <h1 className="text-4xl font-bold mt-4">{post.title || post.clean}</h1>
        <div className="post-meta text-sm text-gray-400 mt-2 flex items-center gap-4">
          <span>By {post.owner?.login || 'unknown'}</span>
          <span>{new Date(post.created_at).toLocaleDateString()}</span>
          {user && user.id === post.owner?.id && (
            <div className="flex items-center gap-4">
              <Link
                to={`/edit/${post.id}`}
                className="text-purple-400 hover:text-purple-300 transition-colors"
              >
                Edit
              </Link>
              <button
                onClick={handleDelete}
                className="text-red-400 hover:text-red-300 transition-colors"
              >
                Delete
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Post content */}
      <div className="post-content prose prose-invert max-w-none">
        {post.feather === 'photo' && post.body?.startsWith('/uploads/') ? (
          <img
            src={`http://127.0.0.1:8000${post.body}`}
            alt={post.title || post.clean}
            className="rounded-lg shadow-md"
          />
        ) : post.feather === 'quote' ? (
          <blockquote className="border-l-4 border-primary-500 pl-4 italic text-lg text-gray-300">
            <ReactMarkdown>{post.body || ''}</ReactMarkdown>
          </blockquote>
        ) : post.feather === 'link' ? (
          <div className="border border-gray-700 rounded-lg p-4 bg-gray-900/50">
            <ReactMarkdown
              components={{
                a: ({ href, children }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary-300 underline font-semibold"
                  >
                    {children} 🔗
                  </a>
                ),
              }}
            >
              {post.body || ''}
            </ReactMarkdown>
          </div>
        ) : (
          <ReactMarkdown>{post.body || ''}</ReactMarkdown>
        )}
      </div>
    </div>
  );
};

export default Post;
