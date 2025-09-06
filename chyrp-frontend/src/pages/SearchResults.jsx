// src/pages/SearchResults.jsx

import { useSearchParams } from 'react-router-dom';
import Cascade from '../components/Cascade';
import PostCard from '../components/PostCard';
import './Home.css';

const SearchResults = () => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q');

  if (!query) {
    return <div className="container"><h1>Please enter a search term.</h1></div>;
  }

  return (
    <div className="home">
      <div className="container">
        <section className="latest-posts">
          <h2>Search results for: "{query}"</h2>
          <Cascade
            endpoint={`/search/posts?q=${encodeURIComponent(query)}`}
            limit={5}
            renderItem={(post) => <PostCard post={post} />}
            className="posts-cascade"
          />
        </section>
      </div>
    </div>
  );
};

export default SearchResults;