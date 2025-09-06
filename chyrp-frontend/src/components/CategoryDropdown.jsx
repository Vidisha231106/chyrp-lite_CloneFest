// src/components/CategoryDropdown.jsx

import { useState, useEffect } from 'react';
import apiClient from '../api';

const CategoryDropdown = ({ selectedCategoryId, onCategoryChange, required = false }) => {
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchCategories = async () => {
            try {
                const response = await apiClient.get('/categories/for-dropdown');
                setCategories(response.data);

                // If no category is selected and categories exist, select the first one
                if (!selectedCategoryId && response.data.length > 0) {
                    onCategoryChange(response.data[0].id);
                }
            } catch (err) {
                setError('Failed to load categories');
                console.error('Error fetching categories:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchCategories();
    }, [selectedCategoryId, onCategoryChange]);

    if (loading) return <select disabled><option>Loading categories...</option></select>;
    if (error) return <select disabled><option>Error loading categories</option></select>;

    return (
        <select
            value={selectedCategoryId || ''}
            onChange={(e) => onCategoryChange(parseInt(e.target.value))}
            required={required}
            className="category-dropdown"
        >
            {!selectedCategoryId && !required && (
                <option value="">Select a category...</option>
            )}
            {categories.map(category => (
                <option key={category.id} value={category.id}>
                    {category.name}
                </option>
            ))}
        </select>
    );
};

export default CategoryDropdown;