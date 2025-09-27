"use client";
import axios from "axios";
import React, { useState, useEffect } from "react";
import { Globe, Clock, ExternalLink, Search, Loader } from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";

// Fallback news data for when API is rate limited
const FALLBACK_NEWS = [
  {
    title: "AI-Powered Legal Aid Platform Launches to Help Underserved Communities",
    description: "A new artificial intelligence platform is making legal assistance more accessible to low-income individuals and families across the country.",
    url: "https://example.com/news/ai-legal-aid",
    image: "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?ixlib=rb-4.0.3&auto=format&fit=crop&w=2942&q=80",
    publishedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    source: { name: "Legal Tech News" }
  },
  {
    title: "Supreme Court Ruling Expands Access to Digital Justice Resources",
    description: "Recent court decisions are paving the way for greater integration of technology in legal proceedings and public access to justice.",
    url: "https://example.com/news/digital-justice",
    image: "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?ixlib=rb-4.0.3&auto=format&fit=crop&w=2942&q=80",
    publishedAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(), // 4 hours ago
    source: { name: "Justice Weekly" }
  },
  {
    title: "Legal Innovation Hub Opens to Support Pro Bono Technology Projects",
    description: "New initiative brings together legal professionals and technologists to develop solutions for access to justice challenges.",
    url: "https://example.com/news/legal-innovation",
    image: "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?ixlib=rb-4.0.3&auto=format&fit=crop&w=2942&q=80",
    publishedAt: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(), // 6 hours ago
    source: { name: "Law & Technology" }
  }
];

const CATEGORIES = [
  {
    id: "all",
    label: "All",
    searchTerms: [
      "legal news",
      "justice",
      "law technology",
      "legal aid",
      "court news",
    ],
  },
  {
    id: "aiLegal",
    label: "AI Legal Tools",
    searchTerms: [
      "AI legal",
      "legal technology",
      "artificial intelligence law",
      "legal software",
      "automated legal",
    ],
  },
  {
    id: "accessJustice",
    label: "Access to Justice",
    searchTerms: [
      "access to justice",
      "legal aid",
      "pro bono",
      "legal assistance",
      "justice reform",
    ],
  },
  {
    id: "underserved",
    label: "Underserved Communities",
    searchTerms: [
      "legal services",
      "community legal aid",
      "rural legal help",
      "low income legal",
      "legal assistance",
    ],
  },
  {
    id: "innovation",
    label: "Legal Innovation",
    searchTerms: [
      "legal innovation",
      "law technology",
      "legal startup",
      "digital law",
      "legal software",
    ],
  },
  {
    id: "impact",
    label: "Social Impact",
    searchTerms: [
      "social justice",
      "legal advocacy",
      "justice reform",
      "legal rights",
      "civil rights",
    ],
  },
  {
    id: "policy",
    label: "Policy & Regulation",
    searchTerms: [
      "legal policy",
      "law regulation",
      "legal reform",
      "justice policy",
      "legal system",
    ],
  },
  {
    id: "education",
    label: "Legal Education",
    searchTerms: [
      "community legal education",
      "know your rights technology",
      "digital legal literacy",
      "self-help legal resources",
      "legal education accessibility",
      "public legal information",
      "legal empowerment tools",
    ],
  },
  {
    id: "partnerships",
    label: "Partnerships",
    searchTerms: [
      "public-private legal partnerships",
      "tech legal aid collaboration",
      "university legal clinic innovations",
      "corporate pro bono technology",
      "nonprofit legal tech alliances",
      "community legal partnerships",
      "cross-sector justice initiatives",
    ],
  },
];

const NewsPage = () => {
  const [selectedCategory, setSelectedCategory] = useState(CATEGORIES[0]);
  const [searchQuery, setSearchQuery] = useState("");
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastFetchTime, setLastFetchTime] = useState(null);
  const { dict } = useLanguage();

  // Cache for storing news data
  const [newsCache, setNewsCache] = useState({});

  const fetchNews = async (category, retryCount = 0) => {
    setLoading(true);
    setError("");
    
    const cacheKey = category.id;
    const now = Date.now();
    const cacheExpiry = 5 * 60 * 1000; // 5 minutes
  
    try {
      // Check cache first
      if (newsCache[cacheKey] && now - newsCache[cacheKey].timestamp < cacheExpiry) {
        console.log("Using cached data for", category.label);
        setNews(newsCache[cacheKey].data);
        setLoading(false);
        return;
      }

      // Rate limiting: Don't make requests too frequently
      if (lastFetchTime && now - lastFetchTime < 2000) {
        console.log("Rate limiting: waiting before next request");
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
  
      // Get API key from environment
      const apiKey = process.env.NEXT_PUBLIC_GNEWS_API_KEY;
      
      if (!apiKey) {
        throw new Error("GNews API key is not configured");
      }
  
      // Construct search terms (simplified to avoid complex queries)
      const primaryTerm = category.searchTerms[0] || "legal news";
      const query = primaryTerm;
      
      // Log the query for debugging
      console.log("Search Query:", query);
  
      // Construct API URL with proper encoding
      const apiUrl = `https://gnews.io/api/v4/search?q=${encodeURIComponent(query)}&lang=en&country=us&max=10&sortby=relevance&apikey=${apiKey}`;
      console.log("API URL:", apiUrl);
  
      // Update last fetch time
      setLastFetchTime(now);

      // Make the API request using Axios with proper headers
      let response = await axios.get(apiUrl, {
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'Law4All/1.0'
        },
        timeout: 15000
      });
  
      // If no articles are found, try the fallback query
      if (!response.data.articles || response.data.articles.length === 0) {
        console.log("No articles found. Trying fallback query...");
        const fallbackQuery = "legal news";
        const fallbackApiUrl = `https://gnews.io/api/v4/search?q=${encodeURIComponent(fallbackQuery)}&lang=en&country=us&max=10&sortby=relevance&apikey=${apiKey}`;
        response = await axios.get(fallbackApiUrl, {
          headers: {
            'Content-Type': 'application/json',
            'User-Agent': 'Law4All/1.0'
          },
          timeout: 10000
        });
      }
  
      // Log the API response for debugging
      console.log("API Response:", response.data);
  
      // Filter valid articles
      const validArticles = (response.data.articles || []).filter(
        (article) =>
          article.title &&
          article.description &&
          article.url &&
          article.publishedAt
      );
  
      // Remove duplicate articles based on URL
      const uniqueArticles = Array.from(
        new Map(validArticles.map((article) => [article.url, article])).values()
      );
  
      // Cache the results
      setNewsCache(prev => ({
        ...prev,
        [cacheKey]: {
          data: uniqueArticles,
          timestamp: now
        }
      }));

      // Update state with the fetched news
      setNews(uniqueArticles);
    } catch (err) {
      // Handle specific error types
      if (err.response) {
        const status = err.response.status;
        console.error("Response data:", err.response.data);
        console.error("Response status:", status);
        console.error("Response headers:", err.response.headers);
        
        if (status === 401) {
          setError("API authentication failed. Please check the API key configuration.");
        } else if (status === 403) {
          setError("API access forbidden. You may have exceeded your daily quota.");
        } else if (status === 429) {
          // Rate limiting - try to use cached data or implement retry with exponential backoff
          if (retryCount < 2) {
            const retryDelay = Math.pow(2, retryCount) * 2000; // 2s, 4s, 8s
            console.log(`Rate limited. Retrying in ${retryDelay}ms...`);
            setError(`Rate limited. Retrying in ${retryDelay / 1000} seconds...`);
            setTimeout(() => {
              fetchNews(category, retryCount + 1);
            }, retryDelay);
            return;
          } else {
            // Check if we have cached data to fall back to
            if (newsCache[cacheKey]) {
              console.log("Using cached data due to rate limiting");
              setNews(newsCache[cacheKey].data);
              setError("Using cached news due to API rate limiting. Data may be outdated.");
            } else {
              // Use fallback news data
              console.log("Using fallback news data due to rate limiting");
              setNews(FALLBACK_NEWS);
              setError("Showing sample news due to API rate limiting. Please try again later for live updates.");
            }
          }
        } else {
          setError(`API error (${status}): ${err.response.data.error || 'Unknown error'}`);
        }
      } else if (err.code === 'ECONNABORTED') {
        setError("Request timed out. Please check your internet connection.");
      } else {
        setError("Failed to fetch news. Please try again later.");
        console.error("Error fetching news:", err.message || err);
      }
    } finally {
      // Reset loading state
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNews(selectedCategory);
  }, [selectedCategory]);

  const filteredNews = news.filter(
    (article) =>
      article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      article.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor(
      (now.getTime() - date.getTime()) / (1000 * 60 * 60)
    );

    if (diffInHours < 1) {
      return "Just now";
    } else if (diffInHours < 24) {
      return `${diffInHours} hours ago`;
    } else {
      return `${Math.floor(diffInHours / 24)} days ago`;
    }
  };

  return (
    <div className="h-full dark:bg-gray-900 py-2 overflow-y-scroll pr-2">
      <div className="mx-auto">
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder={
                  dict?.news?.search_placeholder ||
                  "Search AI legal aid news..."
                }
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-200 dark:border-blue-700 bg-white dark:bg-gray-800 text-blue-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2 overflow-x-auto pb-4 mb-6">
          {CATEGORIES.map((category) => (
            <button
              key={category.id}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                selectedCategory.id === category.id
                  ? "bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400"
                  : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
              }`}
            >
              {dict?.news?.[category.id] || category.label}
            </button>
          ))}
        </div>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader className="h-8 w-8 text-blue-600 animate-spin" />
            <span className="ml-2 text-gray-600 dark:text-gray-400">
              {dict?.news?.loading || "Loading latest legal innovation news..."}
            </span>
          </div>
        )}

        {error && (
          <div className="text-center py-12">
            <p className="text-red-500 dark:text-red-400">{error}</p>
          </div>
        )}

        {!loading && !error && (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-2">
            {filteredNews.map((article, index) => (
              <div
                key={index}
                className="bg-white dark:bg-gray-800 rounded-xl shadow-sm hover:shadow-md transition-shadow overflow-hidden border border-gray-100 dark:border-gray-700"
              >
                <div className="aspect-w-16 aspect-h-9 relative">
                  <img
                    src={
                      article.image ||
                      "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=2942&q=80"
                    }
                    alt={article.title}
                    className="object-cover w-full h-48"
                    onError={(e) => {
                      e.target.src =
                        "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=2942&q=80";
                    }}
                  />
                </div>
                <div className="p-6">
                  <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400 mb-3">
                    <div className="flex items-center">
                      <Clock className="h-4 w-4 mr-1" />
                      {formatDate(article.publishedAt)}
                    </div>
                    <div className="flex items-center">
                      <Globe className="h-4 w-4 mr-1" />
                      {article.source.name}
                    </div>
                  </div>
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">
                    {article.title}
                  </h2>
                  <p className="text-gray-600 dark:text-gray-300 mb-4 line-clamp-3">
                    {article.description}
                  </p>
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-500"
                  >
                    Read full article <ExternalLink className="h-4 w-4 ml-1" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && !error && filteredNews.length === 0 && (
          <div className="text-center py-12 bg-gray-50 dark:bg-gray-800 rounded-xl p-8">
            <h3 className="text-xl font-medium text-gray-700 dark:text-gray-300 mb-2">
              No articles found
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              We couldn't find any news matching your search criteria. Try
              adjusting your search terms or selecting a different category.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default NewsPage;
