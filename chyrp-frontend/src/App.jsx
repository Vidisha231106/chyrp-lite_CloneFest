// src/App.jsx

import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Post from './pages/Post';
import About from './pages/About';
// import Contact from './pages/Contact'; // Assuming you have this file
import Login from './pages/Login';
import Register from './pages/Register';
import CreatePost from './pages/CreatePost';
import EditPost from './pages/EditPost';
import ProtectedRoute from './components/ProtectedRoute';

// 1. Import the new pages you will create
import SearchResults from './pages/SearchResults';
import TagPosts from './pages/TagPosts';
import CategoryPosts from './pages/CategoryPosts';

import './App.css';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
          {/* <Route path="/contact" element={<Contact />} /> */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/posts/:postId" element={<Post />} />

          {/* 2. Add the new routes for search, tags, and categories */}
          <Route path="/search" element={<SearchResults />} />
          <Route path="/tags/:slug" element={<TagPosts />} />
          <Route path="/categories/:slug" element={<CategoryPosts />} />

          {/* Protected Routes */}
          <Route 
            path="/create-post" 
            element={
              <ProtectedRoute>
                <CreatePost />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/edit-post/:postId" 
            element={
              <ProtectedRoute>
                <EditPost />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;