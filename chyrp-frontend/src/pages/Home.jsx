// src/pages/Home.jsx

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api';
import Cascade from '../components/Cascade';
import PostCard from '../components/PostCard';
import './Home.css';

const Home = () => {

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
          <Cascade
            endpoint="/cascade/posts"
            limit={5}
            renderItem={(post) => <PostCard post={post} />}
            className="posts-cascade"
          />
        </section>
      </div>
    </div>
  );
};

export default Home;