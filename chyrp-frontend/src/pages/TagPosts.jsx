// src/pages/TagPosts.jsx

import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import apiClient from '../api';
import Cascade from '../components/Cascade';
import PostCard from '../components/PostCard';
import './Home.css'; // Reuse home page styles

const TagPosts = () => {
  const [tag, setTag] = useState(null);
  const { slug } = useParams();

  useEffect(() => {
    // Fetch tag details to display the name
    const fetchTagInfo = async () => {
      try {
        const response = await apiClient.get(`/tags/slug/${slug}`);
        setTag(response.data);
      } catch (error) {
        console.error("Failed to fetch tag info:", error);
      }
    };
    fetchTagInfo();
  }, [slug]);

  if (!tag) {
    return <div className="container"><h1>Loading posts...</h1></div>;
  }

  return (
    <div className="home">
      <div className="container">
        <section className="latest-posts">
          <h2>Posts tagged with: "{tag.name}"</h2>
          <Cascade
            endpoint={`/tags/${tag.id}/posts`}
            limit={5}
            renderItem={(post) => <PostCard post={post} />}
            className="posts-cascade"
          />
        </section>
      </div>
    </div>
  );
};

export default TagPosts;