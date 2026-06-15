import React, { useState, useEffect, useMemo, useRef } from 'react';
import Papa from 'papaparse';
import Fuse from 'fuse.js';
import { format, isWithinInterval, parseISO, startOfDay, endOfDay } from 'date-fns';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Copy, ArrowUpDown, Search } from 'lucide-react';

interface Review {
  title: string;
  link: string;
  media_type: string;
  post_date: string;
  parenthetical: string;
}

type SortField = 'title' | 'parenthetical' | 'media_type' | 'post_date';
type SortOrder = 'asc' | 'desc';

const normalizeTitle = (title: string) => {
  return title
    .toLowerCase()
    .replace(/^[^\w\s]+/, '') // Remove initial punctuation
    .replace(/^(a|an|the)\s+/, '') // Remove initial articles
    .trim();
};

const App: React.FC = () => {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [titleQuery, setTitleQuery] = useState('');
  const [mediaTypeFilter, setMediaTypeFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // UI State
  const [currentPage, setCurrentPage] = useState(1);
  const [sortField, setSortField] = useState<SortField>('title');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');
  const [toast, setToast] = useState<string | null>(null);
  const [showAutocomplete, setShowAutocomplete] = useState(false);
  
  const autocompleteRef = useRef<HTMLDivElement>(null);
  const pageSize = 10;

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/peter_reviews_data.csv');
        if (!response.ok) throw new Error('Failed to load data');
        const csvText = await response.text();
        
        Papa.parse(csvText, {
          header: true,
          skipEmptyLines: true,
          complete: (results) => {
            setReviews(results.data as Review[]);
            setLoading(false);
          },
          error: (err: Error) => {
            setError(err.message);
            setLoading(false);
          }
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (autocompleteRef.current && !autocompleteRef.current.contains(event.target as Node)) {
        setShowAutocomplete(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const autocompleteOptions = useMemo(() => {
    if (!titleQuery || titleQuery.length < 2) return [];
    
    // Get unique titles
    const uniqueTitles = Array.from(new Set(reviews.map(r => r.title)));
    const fuse = new Fuse(uniqueTitles, {
      includeMatches: true,
      threshold: 0.4,
    });
    
    return fuse.search(titleQuery).slice(0, 8);
  }, [reviews, titleQuery]);

  const filteredAndSortedReviews = useMemo(() => {
    let result = [...reviews];

    // 1. Fuzzy Search by Title
    if (titleQuery) {
      const fuse = new Fuse(result, {
        keys: ['title'],
        threshold: 0.4,
      });
      result = fuse.search(titleQuery).map(r => r.item);
    }

    // 2. Media Type Filter
    if (mediaTypeFilter) {
      result = result.filter(r => r.media_type.toLowerCase() === mediaTypeFilter.toLowerCase());
    }

    // 3. Date Range Filter
    if (startDate || endDate) {
      result = result.filter(r => {
        try {
          const postDate = parseISO(r.post_date);
          const start = startDate ? startOfDay(new Date(startDate)) : new Date(0);
          const end = endDate ? endOfDay(new Date(endDate)) : new Date(8640000000000000);
          return isWithinInterval(postDate, { start, end });
        } catch {
          return true;
        }
      });
    }

    // 4. Multi-level Sorting
    result.sort((a, b) => {
      const compare = (field: SortField, order: SortOrder, rowA: Review, rowB: Review): number => {
        let valA: any, valB: any;
        
        if (field === 'post_date') {
          valA = rowA.post_date ? new Date(rowA.post_date).getTime() : 0;
          valB = rowB.post_date ? new Date(rowB.post_date).getTime() : 0;
        } else if (field === 'title') {
          valA = normalizeTitle(rowA.title);
          valB = normalizeTitle(rowB.title);
        } else {
          valA = (rowA[field] || '').toLowerCase();
          valB = (rowB[field] || '').toLowerCase();
        }

        if (valA < valB) return order === 'asc' ? -1 : 1;
        if (valA > valB) return order === 'asc' ? 1 : -1;
        return 0;
      };

      let cmp = compare(sortField, sortOrder, a, b);
      if (cmp !== 0) return cmp;

      // Secondary sorts
      if (sortField === 'title') {
        // Title -> Date (ASC)
        return compare('post_date', 'asc', a, b);
      } else if (sortField === 'parenthetical' || sortField === 'media_type') {
        // Subtitle/Media Type -> Title (ASC) -> Date (ASC)
        let sec = compare('title', 'asc', a, b);
        if (sec !== 0) return sec;
        return compare('post_date', 'asc', a, b);
      } else if (sortField === 'post_date') {
        // Date -> Title (ASC)
        return compare('title', 'asc', a, b);
      }

      return 0;
    });

    return result;
  }, [reviews, titleQuery, mediaTypeFilter, startDate, endDate, sortField, sortOrder]);

  const paginatedReviews = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredAndSortedReviews.slice(start, start + pageSize);
  }, [filteredAndSortedReviews, currentPage]);

  const totalPages = Math.ceil(filteredAndSortedReviews.length / pageSize);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
    setCurrentPage(1);
  };

  const copyToClipboard = (review: Review) => {
    navigator.clipboard.writeText(review.link).then(() => {
      setToast('Link copied to clipboard!');
      setTimeout(() => setToast(null), 3000);
    });
  };

  const renderBoldedText = (text: string, matches: any) => {
    if (!matches) return text;
    
    // Fuse matches only the first key for uniqueTitles array
    const indices = (matches[0]?.indices as [number, number][]) || [];
    let result: React.ReactNode[] = [];
    let lastIndex = 0;

    indices.forEach(([start, end], i) => {
      result.push(text.substring(lastIndex, start));
      result.push(<strong key={i}>{text.substring(start, end + 1)}</strong>);
      lastIndex = end + 1;
    });
    result.push(text.substring(lastIndex));
    return result;
  };

  if (loading) return <div style={{ textAlign: 'center', marginTop: '5rem' }}>Loading reviews...</div>;
  if (error) return <div style={{ color: 'red', textAlign: 'center', marginTop: '5rem' }}>Error: {error}</div>;

  return (
    <main>
      <h1>Peter's LJ Reviews</h1>
      <p style={{ textAlign: 'center', color: 'var(--color-accent)', marginTop: '-1.5rem', marginBottom: '2rem', opacity: 0.8 }}>
        An archive of media reviews from 2006 to the present.
      </p>

      <section className="filters">
        <div className="filter-group" style={{ position: 'relative' }} ref={autocompleteRef}>
          <label htmlFor="title-search">Title</label>
          <div style={{ position: 'relative' }}>
            <input
              id="title-search"
              type="text"
              placeholder="Search by title..."
              value={titleQuery}
              onChange={(e) => { 
                setTitleQuery(e.target.value); 
                setCurrentPage(1);
                setShowAutocomplete(true);
              }}
              onFocus={() => setShowAutocomplete(true)}
              autoComplete="off"
            />
            <Search size={18} style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', opacity: 0.3 }} />
          </div>
          
          {showAutocomplete && autocompleteOptions.length > 0 && (
            <div className="autocomplete-dropdown">
              {autocompleteOptions.map((opt, i) => (
                <div 
                  key={i} 
                  className="autocomplete-item"
                  onClick={() => {
                    setTitleQuery(opt.item);
                    setShowAutocomplete(false);
                    setCurrentPage(1);
                  }}
                >
                  {renderBoldedText(opt.item, opt.matches)}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="filter-group">
          <label htmlFor="media-type">Media Type</label>
          <select
            id="media-type"
            value={mediaTypeFilter}
            onChange={(e) => { setMediaTypeFilter(e.target.value); setCurrentPage(1); }}
          >
            <option value="">All Types</option>
            <option value="book">Book</option>
            <option value="movie">Movie</option>
            <option value="TV">TV</option>
            <option value="course">Course</option>
            <option value="video game">Video Game</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="start-date">From Date</label>
          <input
            id="start-date"
            type="date"
            value={startDate}
            onChange={(e) => { setStartDate(e.target.value); setCurrentPage(1); }}
          />
        </div>

        <div className="filter-group">
          <label htmlFor="end-date">To Date</label>
          <input
            id="end-date"
            type="date"
            value={endDate}
            onChange={(e) => { setEndDate(e.target.value); setCurrentPage(1); }}
          />
        </div>
      </section>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th onClick={() => handleSort('title')}>
                Title <ArrowUpDown size={14} style={{ marginLeft: '4px' }} />
              </th>
              <th onClick={() => handleSort('parenthetical')}>
                Subtitle <ArrowUpDown size={14} style={{ marginLeft: '4px' }} />
              </th>
              <th onClick={() => handleSort('media_type')}>
                Media Type <ArrowUpDown size={14} style={{ marginLeft: '4px' }} />
              </th>
              <th onClick={() => handleSort('post_date')}>
                Date <ArrowUpDown size={14} style={{ marginLeft: '4px' }} />
              </th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {paginatedReviews.length > 0 ? (
              paginatedReviews.map((review, idx) => (
                <tr key={idx}>
                  <td>
                    <a href={review.link} target="_blank" rel="noopener noreferrer">
                      {review.title}
                    </a>
                  </td>
                  <td>{review.parenthetical}</td>
                  <td style={{ textTransform: 'capitalize' }}>{review.media_type}</td>
                  <td>{review.post_date ? format(parseISO(review.post_date), 'MMM d, yyyy') : 'N/A'}</td>
                  <td>
                    <button className="btn-copy" onClick={() => copyToClipboard(review)} title="Copy Link">
                      <Copy size={14} style={{ marginRight: '4px' }} /> Copy Link
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '3rem', opacity: 0.5 }}>
                  No reviews found matching your filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button
            onClick={() => setCurrentPage(1)}
            disabled={currentPage === 1}
            title="First Page"
          >
            <ChevronsLeft size={20} />
          </button>
          <button
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
            title="Previous Page"
          >
            <ChevronLeft size={20} />
          </button>
          
          <div className="page-jump">
            <span>Page</span>
            <input
              type="number"
              min={1}
              max={totalPages}
              value={currentPage}
              onChange={(e) => {
                const val = parseInt(e.target.value);
                if (!isNaN(val) && val >= 1 && val <= totalPages) {
                  setCurrentPage(val);
                }
              }}
              className="page-input"
            />
            <span>of {totalPages}</span>
          </div>

          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
            title="Next Page"
          >
            <ChevronRight size={20} />
          </button>
          <button
            onClick={() => setCurrentPage(totalPages)}
            disabled={currentPage === totalPages}
            title="Last Page"
          >
            <ChevronsRight size={20} />
          </button>
        </div>
      )}

      {toast && <div className="toast">{toast}</div>}
    </main>
  );
};

export default App;
