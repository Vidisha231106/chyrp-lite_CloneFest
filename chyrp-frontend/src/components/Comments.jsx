// src/components/Comments.jsx

import { useState, useEffect } from 'react';
import apiClient from '../api';
import './Comments.css';

const Comments = ({ postId, currentUser }) => {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [maptchaChallenge, setMaptchaChallenge] = useState(null);
  const [maptchaAnswer, setMaptchaAnswer] = useState('');

  useEffect(() => {
    fetchComments();
    fetchMaptchaChallenge();
  }, [postId]);

  const fetchComments = async () => {
    try {
      const response = await apiClient.get(`/posts/${postId}/comments`);
      setComments(response.data);
    } catch (error) {
      console.error('Failed to fetch comments:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMaptchaChallenge = async () => {
    try {
      const response = await apiClient.post('/maptcha/generate');
      setMaptchaChallenge(response.data);
    } catch (error) {
      console.error('Failed to fetch MAPTCHA challenge:', error);
    }
  };

  const handleSubmitComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    setSubmitting(true);
    try {
      const response = await apiClient.post(`/posts/${postId}/comments/with-maptcha`, {
        body: newComment,
        maptcha_id: maptchaChallenge.id,
        maptcha_answer: maptchaAnswer
      });
      
      setComments([response.data, ...comments]);
      setNewComment('');
      setMaptchaAnswer('');
      fetchMaptchaChallenge(); // Get new challenge
    } catch (error) {
      alert('Failed to submit comment. Please check your answer to the math question.');
      console.error('Comment submission error:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return <div className="comments-section">Loading comments...</div>;
  }

  return (
    <div className="comments-section">
      <h3>Comments ({comments.length})</h3>
      
      {/* Comment Form */}
      <form onSubmit={handleSubmitComment} className="comment-form">
        <div className="form-group">
          <label htmlFor="comment">Add a comment:</label>
          <textarea
            id="comment"
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Write your comment here..."
            rows="4"
            required
          />
        </div>
        
        {/* MAPTCHA Challenge */}
        {maptchaChallenge && (
          <div className="maptcha-challenge">
            <label htmlFor="maptcha-answer">
              Spam protection: {maptchaChallenge.question}
            </label>
            <input
              id="maptcha-answer"
              type="number"
              value={maptchaAnswer}
              onChange={(e) => setMaptchaAnswer(e.target.value)}
              placeholder="Your answer"
              required
            />
          </div>
        )}
        
        <button type="submit" disabled={submitting || !currentUser}>
          {submitting ? 'Submitting...' : 'Submit Comment'}
        </button>
        
        {!currentUser && (
          <p className="login-prompt">
            Please <a href="/login">login</a> to post comments.
          </p>
        )}
      </form>

      {/* Comments List */}
      <div className="comments-list">
        {comments.length === 0 ? (
          <p className="no-comments">No comments yet. Be the first to comment!</p>
        ) : (
          comments.map(comment => (
            <div key={comment.id} className="comment">
              <div className="comment-header">
                <span className="comment-author">{comment.author.login}</span>
                <span className="comment-date">{formatDate(comment.created_at)}</span>
              </div>
              <div className="comment-body">
                {comment.body}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Comments;
