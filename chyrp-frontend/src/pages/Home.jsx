// src/pages/Home.jsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api';

export default function Home() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const res = await apiClient.get('/posts/?content_type=post');
        setPosts(res.data || []);
      } catch (err) {
        console.error('Failed to fetch posts:', err);
        setError('Could not load posts. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchPosts();
  }, []);

  const formatDate = (s) => new Date(s).toLocaleDateString();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-transparent">
        <div className="text-gray-400 animate-pulse">Loading posts…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <p style={{ color: 'red' }}>{error}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-black">
      <div className="max-w-3xl mx-auto px-4 py-12">
        {/* Hero */}
        <section className="text-center mb-12">
          <h1 className="text-5xl md:text-6xl font-extrabold glow-heading animate-hue-spin">
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-primary-400 to-primary-600">
              Chyrp Modern
            </span>
          </h1>
          <p className="mt-4 text-gray-400 max-w-2xl mx-auto">
            A Modern Blogging Website
          </p>
          <div className="mt-6 flex justify-center gap-4">
            <Link to="/create-post" className="btn-primary">Create Post</Link>
            <Link to="/about" className="btn-ghost">Learn more</Link>
          </div>
        </section>

        {/* Latest Posts */}
        <section className="space-y-8">
          {posts.length === 0 && (
            <div className="muted">No posts yet.</div>
          )}

          {posts.map(post => (
            <article
              key={post.id}
              className="card-glass hover:shadow-glow-lg transition-shadow duration-300"
            >
              <div className="flex flex-col gap-4">
                {/* Photo post */}
                {post.feather === 'photo' && post.body?.startsWith('/uploads/') && (
                  <Link
                    to={`/posts/${post.id}`}
                    className="block overflow-hidden rounded-xl"
                  >
                    <img
                      src={`http://127.0.0.1:8000${post.body}`}
                      alt={post.title || post.clean}
                      className="w-full h-72 object-cover transform transition duration-300 hover:scale-105"
                    />
                  </Link>
                )}

                {/* Link post */}
                {post.feather === 'link' && (
                  <div className="border border-gray-700 rounded-lg p-4 bg-gray-900/50">
                    <strong>🔗 Link Post</strong>
                    <br />
                    {(() => {
                      const urlMatch = post.body?.match(/https?:\/\/[^\s]+/);
                      const url = urlMatch ? urlMatch[0] : null;
                      return url ? (
                        <a
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-300 underline font-semibold"
                        >
                          {post.title || 'Shared Link'} 🔗
                        </a>
                      ) : (
                        post.title || 'Shared Link'
                      );
                    })()}
                  </div>
                )}

                {/* Regular text post */}
                {post.feather !== 'photo' && post.feather !== 'link' && (
                  <p className="text-gray-400 mt-2">
                    {post.body
                      ? `${post.body.slice(0, 180)}${
                          post.body.length > 180 ? '...' : ''
                        }`
                      : '—'}
                  </p>
                )}

                {/* Post content */}
                <div>
                  <h3 className="text-2xl font-semibold">
                    <Link
                      to={`/posts/${post.id}`}
                      className="hover:text-primary-300"
                    >
                      {post.title || post.clean}
                    </Link>
                  </h3>

                  <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
                    <div>By {post.owner?.login || 'unknown'}</div>
                    <div>{formatDate(post.created_at)}</div>
                  </div>

                  <div className="mt-4 flex items-center gap-3">
                    <button className="px-3 py-2 rounded-lg bg-primary-600/20 text-primary-200 hover:bg-primary-600/40 transition">
                      ❤️ {post.likes_count || 0}
                    </button>
                    <Link
                      to={`/posts/${post.id}`}
                      className="text-primary-300 hover:underline"
                    >
                      Read more →
                    </Link>
                  </div>
                </div>
              </div>
            </article>
          ))}

          {/* Floating new-post CTA */}
          <div className="fixed bottom-8 right-8">
            <Link
              to="/create-post"
              className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 shadow-glow-lg text-white text-2xl hover:scale-105 transition-transform"
            >
              +
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
