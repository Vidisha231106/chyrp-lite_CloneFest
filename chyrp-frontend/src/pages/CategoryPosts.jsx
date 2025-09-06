// src/pages/CategoryPosts.jsx

import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import apiClient from '../api';
import Cascade from '../components/Cascade';
import PostCard from '../components/PostCard';
import './Home.css'; // Reuse styles from the home page

const CategoryPosts = () => {
    const [category, setCategory] = useState(null);
    const { slug } = useParams(); // Get the category slug from the URL

    useEffect(() => {
        // Fetch the category's details (like its name and ID) using the slug
        const fetchCategoryInfo = async () => {
            try {
                const response = await apiClient.get(`/categories/slug/${slug}`);
                setCategory(response.data);
            } catch (error) {
                console.error("Failed to fetch category info:", error);
            }
        };
        fetchCategoryInfo();
    }, [slug]);

    // Show a loading message until the category details are fetched
    if (!category) {
        return (
            <div className="container" style={{ padding: '2rem' }}>
                <h1>Loading posts...</h1>
            </div>
        );
    }

    return (
        <div className="home">
            <div className="container">
                <section className="latest-posts">
                    {/* Display the category name in the title */}
                    <h2>Posts in category: "{category.name}"</h2>

                    {/* Use the Cascade component to fetch and display posts for this category ID */}
                    <Cascade
                        endpoint={`/categories/${category.id}/posts`}
                        limit={5}
                        renderItem={(post) => <PostCard post={post} />}
                        className="posts-cascade"
                    />
                </section>
            </div>
        </div>
    );
};

export default CategoryPosts;