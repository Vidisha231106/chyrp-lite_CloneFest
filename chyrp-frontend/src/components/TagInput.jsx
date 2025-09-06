// src/components / TagInput.jsx

import { useState } from 'react';

const TagInput = ({ tags, onTagsChange, placeholder = "e.g., python, react, cooking" }) => {
    const [inputValue, setInputValue] = useState('');

    const handleInputChange = (e) => {
        const value = e.target.value;
        setInputValue(value);

        // Convert comma-separated string to array and update parent
        const tagArray = value
            .split(',')
            .map(tag => tag.trim())
            .filter(tag => tag.length > 0);

        onTagsChange(tagArray);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            // Optionally add some logic here for better UX
        }
    };

    return (
        <div className="tag-input-container">
            <input
                type="text"
                value={inputValue}
                onChange={handleInputChange}
                onKeyPress={handleKeyPress}
                placeholder={placeholder}
                className="tag-input"
            />
            <div className="tag-preview">
                {tags.length > 0 && (
                    <div className="tag-preview-list">
                        <small>Tags: </small>
                        {tags.map((tag, index) => (
                            <span key={index} className="tag-preview-item">
                                {tag}
                                {index < tags.length - 1 ? ', ' : ''}
                            </span>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default TagInput;