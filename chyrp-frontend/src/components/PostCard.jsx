import { Link } from 'react-router-dom';

function PostCard({ post }) {
  return (
    <article className="group relative overflow-hidden rounded-2xl bg-dark-card border border-dark-border hover:border-primary-500 transition-all duration-300">
      {post.image && (
        <img 
          src={post.image} 
          alt={post.title}
          className="w-full h-48 object-cover transition-transform duration-300 group-hover:scale-105"
        />
      )}
      <div className="p-6">
        <h3 className="text-xl font-display font-bold text-primary-400 mb-2 group-hover:animate-glow">
          {post.title}
        </h3>
        <p className="text-gray-400 mb-4 line-clamp-2">
          {post.excerpt}
        </p>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">
            {new Date(post.date).toLocaleDateString()}
          </span>
          <Link to={`/posts/${post.id}`} className="btn btn-secondary">
            Read More
          </Link>
        </div>
      </div>
    </article>
  );
}

export default PostCard;