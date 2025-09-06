// src/components/PostCard.jsx

import { Link } from 'react-router-dom';
import './PostCard.css';

const PostCard = ({ post }) => {
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <article className="post-card">
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
              className="post-image"
            />
          </Link>
        ) : post.feather === 'video' ? (
          <div className="post-media">
            <strong>🎥 Video Post</strong><br />
            <video
              controls
              className="post-video"
            >
              <source src={post.body} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
            {post.title && <p className="post-media-title">{post.title}</p>}
          </div>
        ) : post.feather === 'audio' ? (
          <div className="post-media">
            <strong>🎵 Audio Post</strong><br />
            <audio
              controls
              className="post-audio"
            >
              <source src={post.body} type="audio/mpeg" />
              Your browser does not support the audio tag.
            </audio>
            {post.title && <p className="post-media-title">{post.title}</p>}
          </div>
        ) : post.feather === 'link' ? (
          <div className="post-link">
            <strong>🔗 Link Post</strong><br />
            {(() => {
              // Extract URL from the post body
              const urlMatch = post.body?.match(/https?:\/\/[^\s]+/);
              const url = urlMatch ? urlMatch[0] : null;
              return url ? (
                <a href={url} target="_blank" rel="noopener noreferrer" className="post-link-url">
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
          <span className="like-display">❤️ {post.likes_count}</span>
          <span className="view-display">👁️ {post.view_count || 0}</span>
        </div>
        
        {/* Tags and Categories */}
        {(post.tags && post.tags.length > 0) || (post.categories && post.categories.length > 0) ? (
          <div className="post-taxonomy">
            {post.tags && post.tags.length > 0 && (
              <div className="post-tags">
                {post.tags.slice(0, 3).map(tag => (
                  <span key={tag.id} className="tag" style={{ backgroundColor: tag.color }}>
                    {tag.name}
                  </span>
                ))}
                {post.tags.length > 3 && <span className="more-tags">+{post.tags.length - 3} more</span>}
              </div>
            )}
            {post.categories && post.categories.length > 0 && (
              <div className="post-categories">
                {post.categories.map(category => (
                  <span key={category.id} className="category" style={{ backgroundColor: category.color }}>
                    {category.name}
                  </span>
                ))}
              </div>
            )}
          </div>
        ) : null}
        
        <Link to={`/posts/${post.id}`} className="read-more">
          Read More →
        </Link>
      </div>
    </article>
  );
};

export default PostCard;
