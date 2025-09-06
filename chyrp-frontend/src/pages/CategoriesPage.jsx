// src/pages/CategoriesPage.jsx

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import apiClient from '../api';
import './CategoriesPage.css'; // We will create this CSS file next

const CategoriesPage = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await apiClient.get('/categories');
        setCategories(response.data);
      } catch (error) {
        console.error("Failed to fetch categories:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchCategories();
  }, []);

  if (loading) {
    return <div className="container"><h1>Loading Categories...</h1></div>;
  }

  return (
    <div className="categories-page">
      <div className="container">
        <header className="categories-header">
          <h1>Browse by Category</h1>
          <p>Explore posts based on the topics that interest you most.</p>
        </header>
        <div className="category-grid">
          {categories.map(category => (
            <Link to={`/categories/${category.slug}`} key={category.id} className="category-card-link">
              <div className="category-card" style={{ borderTopColor: category.color || '#ddd' }}>
                <h3 className="category-card-name">{category.name}</h3>
                <p className="category-card-description">{category.description}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CategoriesPage;