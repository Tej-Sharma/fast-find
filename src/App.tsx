import React, { useState } from 'react';
import { Search, Globe, Loader2 } from 'lucide-react';
import axios from 'axios';

function App() {
  const [url, setUrl] = useState('');
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);

  const handleSearch = async () => {
    try {
      setIsSearching(true);
      const response = await axios.post('/web-app/deep-find', {
        url,
        query,
        max_links: 200,
        check_interval: 50
      });
      
      setJobId(response.data.long_job_id);
      
      // Start polling for results
      const pollInterval = setInterval(async () => {
        const jobStatus = await axios.get(`/web-app/job-status/${response.data.long_job_id}`);
        if (jobStatus.data.status === 'completed') {
          setResults(jobStatus.data.results);
          setIsSearching(false);
          clearInterval(pollInterval);
        } else if (jobStatus.data.status === 'error') {
          setIsSearching(false);
          clearInterval(pollInterval);
        }
      }, 2000);
      
    } catch (error) {
      console.error('Search failed:', error);
      setIsSearching(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-[#012326] overflow-hidden">
      {/* Background glow effect */}
      <div 
        className="absolute inset-0 bg-gradient-to-b from-[rgba(143,248,255,0.1)] to-transparent"
        style={{
          maskImage: 'radial-gradient(circle at center, black, transparent 80%)',
          WebkitMaskImage: 'radial-gradient(circle at center, black, transparent 80%)'
        }}
      />

      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4">
        {/* Animated Logo */}
        <div className="mb-8">
          <svg width="120" height="120" viewBox="0 0 120 120" className="animate-pulse">
            <defs>
              <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style={{ stopColor: '#8FF8FF', stopOpacity: 0.8 }} />
                <stop offset="100%" style={{ stopColor: '#017B82', stopOpacity: 0.5 }} />
              </linearGradient>
              <filter id="glow">
                <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>
            <g filter="url(#glow)">
              {/* Outer circle */}
              <circle cx="60" cy="60" r="50" 
                fill="none" 
                stroke="url(#logoGradient)" 
                strokeWidth="2"
                className="animate-[spin_10s_linear_infinite]"
              />
              {/* Inner hexagon */}
              <path
                d="M60 25L85 40V70L60 85L35 70V40L60 25Z"
                fill="none"
                stroke="url(#logoGradient)"
                strokeWidth="2"
                className="animate-[spin_5s_linear_infinite]"
              />
              {/* Center circle */}
              <circle cx="60" cy="60" r="15" 
                fill="none" 
                stroke="url(#logoGradient)" 
                strokeWidth="2"
              />
              {/* Connecting lines */}
              <line x1="60" y1="25" x2="60" y2="45" stroke="url(#logoGradient)" strokeWidth="2" />
              <line x1="85" y1="40" x2="75" y2="55" stroke="url(#logoGradient)" strokeWidth="2" />
              <line x1="85" y1="70" x2="75" y2="65" stroke="url(#logoGradient)" strokeWidth="2" />
              <line x1="60" y1="85" x2="60" y2="75" stroke="url(#logoGradient)" strokeWidth="2" />
              <line x1="35" y1="70" x2="45" y2="65" stroke="url(#logoGradient)" strokeWidth="2" />
              <line x1="35" y1="40" x2="45" y2="55" stroke="url(#logoGradient)" strokeWidth="2" />
            </g>
          </svg>
        </div>

        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-6" style={{
            background: 'linear-gradient(90deg, rgba(255, 255, 255, 0.80) -9.85%, rgba(129, 255, 254, 0.50) 99.95%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            textShadow: '0px 0px 16px rgba(255, 255, 255, 0.32)'
          }}>
            Quickly find something across thousands of links
          </h1>
          <p className="text-xl" style={{
            background: 'linear-gradient(90deg, rgba(255, 255, 255, 0.72) 0%, rgba(255, 255, 255, 0.36) 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            Deep search through any website's content in seconds
          </p>
        </div>

        <div className="w-full max-w-4xl p-8 rounded-2xl" style={{
          background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.08) 0%, rgba(1, 123, 130, 0.08) 100%)',
          backdropFilter: 'blur(24px)',
          border: '1px solid rgba(143, 248, 255, 0.2)',
          boxShadow: '0px 8px 32px 0px rgba(0, 0, 0, 0.32)'
        }}>
          <div className="space-y-4">
            <div className="relative">
              <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#8FF8FF]" />
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Enter website URL"
                className="w-full pl-12 pr-4 py-4 bg-[rgba(255,255,255,0.05)] rounded-xl border border-[rgba(143,248,255,0.2)] text-white placeholder-[rgba(255,255,255,0.5)] focus:outline-none focus:border-[#8FF8FF] transition-colors"
                style={{ backdropFilter: 'blur(12px)' }}
              />
            </div>
            
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#8FF8FF]" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="What are you looking for?"
                className="w-full pl-12 pr-4 py-4 bg-[rgba(255,255,255,0.05)] rounded-xl border border-[rgba(143,248,255,0.2)] text-white placeholder-[rgba(255,255,255,0.5)] focus:outline-none focus:border-[#8FF8FF] transition-colors"
                style={{ backdropFilter: 'blur(12px)' }}
              />
            </div>

            <button
              onClick={handleSearch}
              disabled={isSearching || !url || !query}
              className="w-full py-4 rounded-xl flex items-center justify-center gap-2 transition-all"
              style={{
                background: 'linear-gradient(180deg, rgba(255, 255, 255, 0.50) 0%, rgba(1, 123, 130, 0.70) 11.21%, #017B82 42.19%, #017B82 47.13%, #035256 100%)',
                border: '2px solid #8FF8FF',
                boxShadow: '0px -8px 16px 0px rgba(93, 218, 225, 0.63), 0px 8px 32px 0px rgba(143, 248, 255, 0.40) inset'
              }}
            >
              {isSearching ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  <span>Search Deep</span>
                </>
              )}
            </button>
          </div>

          {results && (
            <div className="mt-8 p-6 rounded-xl bg-[rgba(255,255,255,0.03)] border border-[rgba(143,248,255,0.1)]">
              <pre className="text-[rgba(255,255,255,0.8)] overflow-auto">
                {JSON.stringify(results, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Hero Image */}
        <div className="w-full max-w-6xl mt-16 relative">
          <img
            src="https://images.unsplash.com/photo-1633356122544-f134324a6cee?auto=format&fit=crop&w=2070&q=80"
            alt="Network visualization"
            className="w-full h-auto rounded-2xl"
            style={{
              border: '1px solid rgba(143, 248, 255, 0.2)',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
              opacity: 0.9
            }}
          />
          <div
            className="absolute inset-0 rounded-2xl"
            style={{
              background: 'linear-gradient(180deg, rgba(1, 35, 38, 0) 0%, rgba(1, 35, 38, 0.8) 100%)',
              mixBlendMode: 'multiply'
            }}
          />
        </div>
      </div>
    </div>
  );
}

export default App;