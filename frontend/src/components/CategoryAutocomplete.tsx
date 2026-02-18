import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { categoriesApi } from '@/api/client';
import { Category } from '@/types';

interface CategoryAutocompleteProps {
  value: string;
  onChange: (value: string) => void;
  label?: string;
  required?: boolean;
}

export const CategoryAutocomplete = ({
  value,
  onChange,
  label,
  required = false,
}: CategoryAutocompleteProps) => {
  const { t } = useTranslation();
  const [suggestions, setSuggestions] = useState<Category[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Use provided label or default from i18n
  const displayLabel = label || t('transaction.category');

  const fetchSuggestions = useCallback(async (query: string) => {
    if (query.length < 1) {
      setSuggestions([]);
      return;
    }

    setIsLoading(true);
    try {
      const data = await categoriesApi.search(query);
      setSuggestions(data);
    } catch (error) {
      console.error('Failed to fetch suggestions:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchSuggestions(value);
    }, 300); // Debounce 300ms

    return () => clearTimeout(timer);
  }, [value, fetchSuggestions]);

  const handleSelect = (categoryName: string) => {
    onChange(categoryName);
    setShowSuggestions(false);
  };

  return (
    <div className="relative">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {displayLabel}
        {required && <span className="text-danger-500 ml-1">*</span>}
      </label>
      <input
        type="text"
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setShowSuggestions(true);
        }}
        onFocus={() => setShowSuggestions(true)}
        onBlur={() => {
          // Delay hiding to allow click on suggestions
          setTimeout(() => setShowSuggestions(false), 200);
        }}
        className="input"
        placeholder={t('transaction.searchCategory')}
        required={required}
        autoComplete="off"
      />
      
      {isLoading && (
        <div className="absolute right-3 top-9">
          <div className="animate-spin h-4 w-4 border-2 border-primary-600 border-t-transparent rounded-full"></div>
        </div>
      )}

      {showSuggestions && suggestions.length > 0 && (
        <ul className="absolute z-10 w-full mt-1 bg-white shadow-lg rounded-lg border border-gray-200 max-h-48 overflow-auto">
          {suggestions.map((category) => (
            <li
              key={category.id}
              onClick={() => handleSelect(category.name)}
              className="px-4 py-2 hover:bg-gray-100 cursor-pointer text-sm text-gray-700"
            >
              {category.name}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
