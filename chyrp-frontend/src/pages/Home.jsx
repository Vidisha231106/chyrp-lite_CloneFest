// src/pages/Home.jsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api';
import Cascade from '../components/Cascade';
import PostCard from '../components/PostCard';
import './Home.css';

const Home = () => {

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
}

export default Home;