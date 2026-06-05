import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip as ChartTooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { 
  TrendingUp, Users, Settings, Database, Upload, AlertCircle, 
  ChevronLeft, ArrowUpDown, HelpCircle, Check, Trash, Plus,ExternalLink
} from 'lucide-react';

const API_BASE = '/api';

export default function App() {
  const [currentView, setCurrentView] = useState('dashboard'); // 'dashboard' | 'trends' | 'developer' | 'admin'
  const [periods, setPeriods] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState('');
  const [periodType, setPeriodType] = useState('monthly'); // 'weekly' | 'monthly'
  const [weeklySpendApproximated, setWeeklySpendApproximated] = useState(false);
  
  // Leaderboard data
  const [leaderboardMetrics, setLeaderboardMetrics] = useState([]);
  const [flagFilters, setFlagFilters] = useState({ green: true, red: true, yellow: true, gray: true });
  const [sortField, setSortField] = useState('flag');
  const [sortOrder, setSortOrder] = useState('asc'); // 'asc' | 'desc'
  
  // Developer Profile data
  const [selectedDevEmail, setSelectedDevEmail] = useState('');
  const [devProfile, setDevProfile] = useState(null);
  
  // Team Trends data
  const [teamTrends, setTeamTrends] = useState([]);
  
  // Settings & Mapping
  const [runs, setRuns] = useState([]);
  const [jiraBaseUrl, setJiraBaseUrl] = useState('');
  const [developersMap, setDevelopersMap] = useState([]);
  const [newDevName, setNewDevName] = useState('');
  const [newDevEmail, setNewDevEmail] = useState('');

  // Upload state
  const [uploadPeriodType, setUploadPeriodType] = useState('monthly');
  const [uploadPeriodValue, setUploadPeriodValue] = useState('');
  const [claudeFile, setClaudeFile] = useState(null);
  const [jiraDelivFile, setJiraDelivFile] = useState(null);
  const [jiraBugsFile, setJiraBugsFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isServerRunning, setIsServerRunning] = useState(false);
  const [serverPeriodValue, setServerPeriodValue] = useState('');

  // Notifications
  const [notification, setNotification] = useState(null);

  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4000);
  };

  // 1. Fetch periods & config on mount
  useEffect(() => {
    fetchPeriods();
    fetchSettings();
    fetchDevelopersMap();
    fetchRuns();
  }, []);

  const fetchPeriods = async () => {
    try {
      const res = await fetch(`${API_BASE}/periods`);
      const data = await res.json();
      setPeriods(data.periods || []);
      
      // Auto-select latest period if not set
      if (data.periods && data.periods.length > 0) {
        const sorted = [...data.periods].sort();
        const latest = sorted[sorted.length - 1];
        setSelectedPeriod(latest);
        
        // Auto-detect period type of latest
        if (latest.includes('-W')) {
          setPeriodType('weekly');
        } else {
          setPeriodType('monthly');
        }
      }
    } catch (e) {
      console.error("Failed to fetch periods:", e);
    }
  };

  const fetchSettings = async () => {
    try {
      const res = await fetch(`${API_BASE}/settings`);
      const data = await res.json();
      setJiraBaseUrl(data.jira_base_url || '');
    } catch (e) {
      console.error("Failed to fetch settings:", e);
    }
  };

  const fetchDevelopersMap = async () => {
    try {
      const res = await fetch(`${API_BASE}/developers`);
      const data = await res.json();
      setDevelopersMap(data.developers || []);
    } catch (e) {
      console.error("Failed to fetch developers map:", e);
    }
  };

  const fetchRuns = async () => {
    try {
      const res = await fetch(`${API_BASE}/runs`);
      const data = await res.json();
      setRuns(data.runs || []);
    } catch (e) {
      console.error("Failed to fetch runs:", e);
    }
  };

  // 2. Load leaderboard data when selectedPeriod changes
  useEffect(() => {
    if (selectedPeriod) {
      fetchLeaderboard(selectedPeriod);
    }
  }, [selectedPeriod]);

  const fetchLeaderboard = async (period) => {
    try {
      const res = await fetch(`${API_BASE}/leaderboard?period=${period}`);
      const data = await res.json();
      setLeaderboardMetrics(data.metrics || []);
      setWeeklySpendApproximated(data.weekly_spend_approximated || false);
    } catch (e) {
      console.error("Failed to fetch leaderboard:", e);
    }
  };

  // 3. Load developer profile
  const fetchDevProfile = async (email, period) => {
    try {
      const res = await fetch(`${API_BASE}/developer/${email}?period=${period}`);
      const data = await res.json();
      setDevProfile(data);
    } catch (e) {
      console.error("Failed to fetch developer profile:", e);
    }
  };

  // 4. Load team trends
  const fetchTeamTrends = async () => {
    try {
      const res = await fetch(`${API_BASE}/team/trends`);
      const data = await res.json();
      setTeamTrends(data.trends || []);
    } catch (e) {
      console.error("Failed to fetch team trends:", e);
    }
  };

  useEffect(() => {
    if (currentView === 'trends') {
      fetchTeamTrends();
    } else if (currentView === 'admin') {
      fetchRuns();
      fetchDevelopersMap();
    }
  }, [currentView]);

  // Handle period toggle filtering
  const filteredPeriods = periods.filter(p => {
    const isWeek = p.includes('-W');
    return periodType === 'weekly' ? isWeek : !isWeek;
  });

  // Sort Metrics logic
  const sortMetrics = (a, b) => {
    let valA = a[sortField];
    let valB = b[sortField];

    // Treat flag severity specially
    if (sortField === 'flag') {
      const severity = { red: 0, gray: 1, yellow: 2, green: 3 };
      valA = severity[a.flag] ?? 4;
      valB = severity[b.flag] ?? 4;
    }

    // Handle null values
    if (valA === null || valA === undefined) return sortOrder === 'asc' ? 1 : -1;
    if (valB === null || valB === undefined) return sortOrder === 'asc' ? -1 : 1;

    if (typeof valA === 'string') {
      return sortOrder === 'asc' 
        ? valA.localeCompare(valB) 
        : valB.localeCompare(valA);
    } else {
      return sortOrder === 'asc' ? valA - valB : valB - valA;
    }
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc'); // Default to descending for numeric values
    }
  };

  // Filter leaderboard
  const displayedMetrics = leaderboardMetrics
    .filter(m => flagFilters[m.flag])
    .sort(sortMetrics);

  // Summary Metrics calculations
  const totalTokensSpend = leaderboardMetrics.reduce((sum, m) => sum + (m.spend_usd || 0), 0);
  const totalDeliverables = leaderboardMetrics.reduce((sum, m) => sum + (m.deliverables_count || 0), 0);
  const validEfficiencies = leaderboardMetrics.filter(m => m.ai_efficiency_score !== null);
  const avgEfficiency = validEfficiencies.length > 0 
    ? (validEfficiencies.reduce((sum, m) => sum + m.ai_efficiency_score, 0) / validEfficiencies.length).toFixed(3)
    : 'N/A';

  const flagCounts = leaderboardMetrics.reduce((acc, m) => {
    if (m.flag in acc) acc[m.flag]++;
    return acc;
  }, { green: 0, red: 0, yellow: 0, gray: 0 });

  // Handle config form submit
  const saveJiraConfig = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jira_base_url: jiraBaseUrl })
      });
      if (res.ok) {
        showNotification("Jira base URL updated successfully!");
      }
    } catch (e) {
      showNotification("Failed to update Settings.", 'error');
    }
  };

  // Handle Developer Mapping add / delete / save
  const addDeveloperToMap = () => {
    if (!newDevName || !newDevEmail) {
      showNotification("Please fill in both name and email.", 'error');
      return;
    }
    setDevelopersMap([...developersMap, { display_name: newDevName, email: newDevEmail }]);
    setNewDevName('');
    setNewDevEmail('');
  };

  const removeDeveloperFromMap = (index) => {
    const updated = [...developersMap];
    updated.splice(index, 1);
    setDevelopersMap(updated);
  };

  const saveDevelopersMap = async () => {
    try {
      const res = await fetch(`${API_BASE}/developers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(developersMap)
      });
      if (res.ok) {
        showNotification("Developer mappings saved successfully!");
      }
    } catch (e) {
      showNotification("Failed to save mappings.", 'error');
    }
  };

  // Handle Manual File Upload Ingestion
  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!uploadPeriodValue || !claudeFile || !jiraDelivFile || !jiraBugsFile) {
      showNotification("Please select a period and attach all three files.", 'error');
      return;
    }

    const formData = new FormData();
    formData.append("period", uploadPeriodValue);
    formData.append("claude_file", claudeFile);
    formData.append("jira_deliverables_file", jiraDelivFile);
    formData.append("jira_bugs_file", jiraBugsFile);

    setIsUploading(true);
    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        showNotification(`Ingestion successful for ${uploadPeriodValue}! Computed metrics for ${data.developers_count} developers.`);
        // Reset inputs
        setUploadPeriodValue('');
        setClaudeFile(null);
        setJiraDelivFile(null);
        setJiraBugsFile(null);
        // Refresh data
        await fetchPeriods();
        await fetchRuns();
      } else {
        showNotification(data.detail || "Upload failed.", 'error');
      }
    } catch (e) {
      showNotification("Ingestion processing encountered an error.", 'error');
    } finally {
      setIsUploading(false);
    }
  };

  // Handle Server-Side run
  const handleServerRun = async (e) => {
    e.preventDefault();
    if (!serverPeriodValue) {
      showNotification("Please specify a period YYYY-MM or YYYY-Www.", 'error');
      return;
    }

    setIsServerRunning(true);
    try {
      const res = await fetch(`${API_BASE}/run-server?period=${serverPeriodValue}`, {
        method: 'POST'
      });
      const data = await res.json();
      if (res.ok) {
        showNotification(`Server-side ingestion completed successfully! Computed metrics for ${data.developers_count} developers.`);
        setServerPeriodValue('');
        await fetchPeriods();
        await fetchRuns();
      } else {
        showNotification(data.detail || "Server pipeline run failed.", 'error');
      }
    } catch (e) {
      showNotification("Server run failed.", 'error');
    } finally {
      setIsServerRunning(false);
    }
  };

  const handleDeveloperClick = (email) => {
    setSelectedDevEmail(email);
    fetchDevProfile(email, selectedPeriod);
    setCurrentView('developer');
  };

  const handlePeriodChange = (val) => {
    setSelectedPeriod(val);
  };

  const togglePeriodType = (type) => {
    setPeriodType(type);
    
    // Find first period of that type and select it
    const options = periods.filter(p => {
      const isWeek = p.includes('-W');
      return type === 'weekly' ? isWeek : !isWeek;
    });
    if (options.length > 0) {
      setSelectedPeriod(options[0]);
    } else {
      setSelectedPeriod('');
    }
  };

  return (
    <div className="app-container">
      {/* Toast Notification */}
      {notification && (
        <div 
          style={{
            position: 'fixed', top: '24px', right: '24px', zIndex: 1000,
            display: 'flex', alignItems: 'center', gap: '8px',
            backgroundColor: notification.type === 'error' ? '#ef4444' : '#10b981',
            color: '#fff', padding: '12px 20px', borderRadius: '8px',
            boxShadow: '0 10px 15px -3px rgba(0,0,0,0.3)',
            animation: 'spin 0.2s linear'
          }}
        >
          {notification.type === 'error' && <AlertCircle size={18} />}
          {notification.type === 'success' && <Check size={18} />}
          <span style={{ fontSize: '14px', fontWeight: '500' }}>{notification.message}</span>
        </div>
      )}

      {/* Header */}
      <header className="app-header">
        <div className="brand">
          <TrendingUp size={28} color="#6366f1" />
          <h1 className="brand-title">Developer productivity dashboard</h1>
        </div>
        <nav className="nav-links">
          <button 
            className={`nav-btn ${currentView === 'dashboard' ? 'active' : ''}`}
            onClick={() => { setCurrentView('dashboard'); if (selectedPeriod) fetchLeaderboard(selectedPeriod); }}
          >
            <Users size={16} /> Leaderboard
          </button>
          <button 
            className={`nav-btn ${currentView === 'trends' ? 'active' : ''}`}
            onClick={() => setCurrentView('trends')}
          >
            <TrendingUp size={16} /> Team Trends
          </button>
          <button 
            className={`nav-btn ${currentView === 'admin' ? 'active' : ''}`}
            onClick={() => setCurrentView('admin')}
          >
            <Database size={16} /> Data & Ingestion
          </button>
        </nav>
      </header>

      {/* MAIN VIEWPORT */}
      <main style={{ display: 'flex', flexDirection: 'column', gap: '24px', minHeight: '60vh' }}>
        
        {/* Onboarding State if database is empty */}
        {periods.length === 0 && currentView !== 'admin' && (
          <div className="glass-card" style={{ textAlign: 'center', padding: '48px 24px' }}>
            <Database size={64} style={{ color: 'var(--text-secondary)', marginBottom: '16px', opacity: 0.5 }} />
            <h2 style={{ marginBottom: '8px' }}>No Data Available</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '24px', maxWidth: '500px', marginInline: 'auto' }}>
              The productivity dashboard database is currently empty. Please go to the Data & Ingestion page to upload your initial Claude and JIRA CSV data exports.
            </p>
            <button className="btn" onClick={() => setCurrentView('admin')}>
              <Database size={16} /> Go to Ingestion
            </button>
          </div>
        )}

        {/* 1. TEAM DASHBOARD / LEADERBOARD VIEW */}
        {periods.length > 0 && currentView === 'dashboard' && (
          <>
            {/* Filter Bar */}
            <div className="glass-card filter-bar">
              <div className="filter-group">
                <div className="toggle-group">
                  <button 
                    className={`toggle-btn ${periodType === 'monthly' ? 'active' : ''}`}
                    onClick={() => togglePeriodType('monthly')}
                  >
                    Monthly
                  </button>
                  <button 
                    className={`toggle-btn ${periodType === 'weekly' ? 'active' : ''}`}
                    onClick={() => togglePeriodType('weekly')}
                  >
                    Weekly
                  </button>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Period:</label>
                  <select 
                    value={selectedPeriod} 
                    onChange={(e) => handlePeriodChange(e.target.value)}
                    style={{ minWidth: '130px' }}
                  >
                    {filteredPeriods.map(p => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Checkbox filters */}
              <div className="filter-group">
                <label style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Filter Flags:</label>
                <div className="flag-checkboxes">
                  <label className={`flag-checkbox-label ${flagFilters.green ? 'active-green' : ''}`}>
                    <input 
                      type="checkbox" 
                      checked={flagFilters.green}
                      onChange={(e) => setFlagFilters({ ...flagFilters, green: e.target.checked })}
                      style={{ display: 'none' }}
                    />
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--flag-green)' }}></span>
                    On Track ({flagCounts.green})
                  </label>
                  <label className={`flag-checkbox-label ${flagFilters.red ? 'active-red' : ''}`}>
                    <input 
                      type="checkbox" 
                      checked={flagFilters.red}
                      onChange={(e) => setFlagFilters({ ...flagFilters, red: e.target.checked })}
                      style={{ display: 'none' }}
                    />
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--flag-red)' }}></span>
                    Quality Risk ({flagCounts.red})
                  </label>
                  <label className={`flag-checkbox-label ${flagFilters.yellow ? 'active-yellow' : ''}`}>
                    <input 
                      type="checkbox" 
                      checked={flagFilters.yellow}
                      onChange={(e) => setFlagFilters({ ...flagFilters, yellow: e.target.checked })}
                      style={{ display: 'none' }}
                    />
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--flag-yellow)' }}></span>
                    Coaching ({flagCounts.yellow})
                  </label>
                  <label className={`flag-checkbox-label ${flagFilters.gray ? 'active-gray' : ''}`}>
                    <input 
                      type="checkbox" 
                      checked={flagFilters.gray}
                      onChange={(e) => setFlagFilters({ ...flagFilters, gray: e.target.checked })}
                      style={{ display: 'none' }}
                    />
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--flag-gray)' }}></span>
                    Attention ({flagCounts.gray})
                  </label>
                </div>
              </div>
            </div>

            {/* Weekly Fallback warning */}
            {weeklySpendApproximated && (
              <div className="warning-banner">
                <AlertCircle size={18} />
                <span>
                  <strong>Note:</strong> Claude Console spend is currently approximated for this weekly view (divided by 4.3) because only monthly exports were available.
                </span>
              </div>
            )}

            {/* Summary Cards */}
            <div className="metrics-grid">
              <div className="glass-card metric-card">
                <span className="metric-label">Total Spend</span>
                <span className="metric-value">
                  ${totalTokensSpend.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
              <div className="glass-card metric-card">
                <span className="metric-label">Deliverables Count</span>
                <span className="metric-value">
                  {totalDeliverables}
                  <span className="metric-unit">closed</span>
                </span>
              </div>
              <div className="glass-card metric-card">
                <span className="metric-label">Avg AI Efficiency</span>
                <span className="metric-value">
                  {avgEfficiency}
                  <span className="metric-unit">SP/$</span>
                </span>
              </div>
              <div className="glass-card metric-card">
                <span className="metric-label">Quality Risk Devs</span>
                <span className="metric-value" style={{ color: flagCounts.red > 0 ? 'var(--flag-red)' : 'var(--text-primary)' }}>
                  {flagCounts.red}
                  <span className="metric-unit" style={{ color: 'var(--text-secondary)' }}>developers</span>
                </span>
              </div>
            </div>

            {/* Table Leaderboard */}
            <div className="glass-card">
              <h2 style={{ marginBottom: '16px' }}>Developer Leaderboard — {selectedPeriod}</h2>
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th onClick={() => handleSort('display_name')}>Developer Name <ArrowUpDown size={12} style={{ marginLeft: '4px', display: 'inline' }} /></th>
                      <th onClick={() => handleSort('spend_usd')} style={{ textAlign: 'right' }}>Spend ($) <ArrowUpDown size={12} style={{ marginLeft: '4px', display: 'inline' }} /></th>
                      <th onClick={() => handleSort('lines_of_code')} style={{ textAlign: 'right' }}>Lines written <ArrowUpDown size={12} style={{ marginLeft: '4px', display: 'inline' }} /></th>
                      <th onClick={() => handleSort('deliverables_count')} style={{ textAlign: 'right' }}>Deliverables <ArrowUpDown size={12} style={{ marginLeft: '4px', display: 'inline' }} /></th>
                      <th onClick={() => handleSort('story_points_delivered')} style={{ textAlign: 'right' }}>Story Points <ArrowUpDown size={12} style={{ marginLeft: '4px', display: 'inline' }} /></th>
                      <th onClick={() => handleSort('story_points_coverage')} style={{ textAlign: 'right' }}>SP Coverage <ArrowUpDown size={12} style={{ marginLeft: '4px', display: 'inline' }} /></th>
                      <th onClick={() => handleSort('ai_efficiency_score')} style={{ textAlign: 'right' }}>AI Efficiency <ArrowUpDown size={12} style={{ marginLeft: '4px', display: 'inline' }} /></th>
                      <th onClick={() => handleSort('bugs_attributed')} style={{ textAlign: 'right' }}>Attributed Bugs <ArrowUpDown size={12} style={{ marginLeft: '4px', display: 'inline' }} /></th>
                      <th onClick={() => handleSort('bug_rate')} style={{ textAlign: 'right' }}>Bug Rate <ArrowUpDown size={12} style={{ marginLeft: '4px', display: 'inline' }} /></th>
                      <th onClick={() => handleSort('flag')} style={{ textAlign: 'center' }}>Flag <ArrowUpDown size={12} style={{ marginLeft: '4px', display: 'inline' }} /></th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayedMetrics.length === 0 ? (
                      <tr>
                        <td colSpan="10" style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '24px' }}>
                          No developers match the active flag filters.
                        </td>
                      </tr>
                    ) : (
                      displayedMetrics.map(m => (
                        <tr key={m.email}>
                          <td>
                            <div style={{ display: 'flex', flexDirection: 'column' }}>
                              <span 
                                className="table-link"
                                onClick={() => handleDeveloperClick(m.email)}
                              >
                                {m.display_name}
                              </span>
                              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{m.email}</span>
                            </div>
                          </td>
                          <td style={{ textAlign: 'right', fontWeight: '500' }}>
                            ${m.spend_usd.toFixed(2)}
                          </td>
                          <td style={{ textAlign: 'right' }}>{m.lines_of_code.toLocaleString()}</td>
                          <td style={{ textAlign: 'right' }}>{m.deliverables_count}</td>
                          <td style={{ textAlign: 'right' }}>{m.story_points_delivered}</td>
                          <td style={{ textAlign: 'right', color: m.story_points_coverage < 0.8 ? 'var(--flag-yellow)' : 'var(--text-primary)' }}>
                            {(m.story_points_coverage * 100).toFixed(0)}%
                          </td>
                          <td style={{ textAlign: 'right', fontWeight: '600' }}>
                            {m.ai_efficiency_score !== null 
                              ? m.ai_efficiency_score.toFixed(3) 
                              : <span style={{ color: 'var(--flag-yellow)' }} title="Story points missing on >20% of tickets">N/A ⚠️</span>}
                          </td>
                          <td style={{ textAlign: 'right' }}>{m.bugs_attributed}</td>
                          <td style={{ textAlign: 'right' }}>
                            {m.bug_rate !== null ? `${(m.bug_rate * 100).toFixed(0)}%` : '0%'}
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            <span className={`badge badge-${m.flag}`}>
                              {m.flag === 'green' && 'On Track'}
                              {m.flag === 'red' && 'Quality Risk'}
                              {m.flag === 'yellow' && 'Coaching'}
                              {m.flag === 'gray' && 'Needs Attn'}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* In-Line Scoring Info */}
            <div className="info-card" style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
              <HelpCircle size={18} style={{ color: 'var(--accent-primary)', flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong>How Scoring Works:</strong>
                <ul style={{ paddingLeft: '16px', marginTop: '4px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  <li><strong>AI Efficiency Score:</strong> Calculated as `Story Points Delivered ÷ Spend USD`. Suppressed to `N/A ⚠️` if story points are missing on 20% or more deliverables.</li>
                  <li><strong>Flags Calculation:</strong> Computed using team medians. 🟢 <em>On Track</em> (High efficiency, Low bug rate), 🔴 <em>Quality Risk</em> (High efficiency, High bug rate), 🟡 <em>Coaching Opportunity</em> (Low efficiency, Low bug rate), ⚪ <em>Needs Attention</em> (Low efficiency, High bug rate).</li>
                </ul>
              </div>
            </div>
          </>
        )}

        {/* 2. DEVELOPER PROFILE PAGE VIEW */}
        {currentView === 'developer' && devProfile && (
          <div className="profile-grid">
            {/* Sidebar Details */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <button 
                className="btn btn-secondary" 
                onClick={() => setCurrentView('dashboard')}
                style={{ width: '100%' }}
              >
                <ChevronLeft size={16} /> Back to Leaderboard
              </button>

              <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div>
                  <h2 style={{ fontSize: '20px', marginBottom: '2px' }}>{devProfile.profile ? devProfile.profile.display_name : selectedDevEmail}</h2>
                  <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{selectedDevEmail}</span>
                </div>

                <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Current Flag</span>
                    <div style={{ marginTop: '4px' }}>
                      {devProfile.profile ? (
                        <span className={`badge badge-${devProfile.profile.flag}`} style={{ padding: '6px 12px', fontSize: '13px' }}>
                          {devProfile.profile.flag === 'green' && '🟢 On Track'}
                          {devProfile.profile.flag === 'red' && '🔴 Quality Risk'}
                          {devProfile.profile.flag === 'yellow' && '🟡 Coaching Opportunity'}
                          {devProfile.profile.flag === 'gray' && '⚪ Needs Attention'}
                        </span>
                      ) : (
                        <span className="badge badge-gray">No Flag Data</span>
                      )}
                    </div>
                  </div>

                  <div className="info-card" style={{ fontSize: '12px', background: 'rgba(255,255,255,0.01)', border: '1px dashed var(--card-border)' }}>
                    {devProfile.explanation}
                  </div>
                </div>
              </div>

              {/* Current Period stats */}
              {devProfile.profile && (
                <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <h3 style={{ fontSize: '14px', textTransform: 'uppercase', color: 'var(--text-secondary)', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '6px' }}>
                    {selectedPeriod} Stats
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div>
                      <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Claude Spend</span>
                      <p style={{ fontSize: '18px', fontWeight: '600' }}>${devProfile.profile.spend_usd.toFixed(2)}</p>
                    </div>
                    <div>
                      <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Lines of Code</span>
                      <p style={{ fontSize: '18px', fontWeight: '600' }}>{devProfile.profile.lines_of_code.toLocaleString()}</p>
                    </div>
                    <div>
                      <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Deliverables</span>
                      <p style={{ fontSize: '18px', fontWeight: '600' }}>{devProfile.profile.deliverables_count}</p>
                    </div>
                    <div>
                      <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Story Points</span>
                      <p style={{ fontSize: '18px', fontWeight: '600' }}>{devProfile.profile.story_points_delivered}</p>
                    </div>
                    <div>
                      <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>SP Coverage</span>
                      <p style={{ fontSize: '18px', fontWeight: '600' }}>{(devProfile.profile.story_points_coverage * 100).toFixed(0)}%</p>
                    </div>
                    <div>
                      <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Efficiency</span>
                      <p style={{ fontSize: '18px', fontWeight: '600' }}>
                        {devProfile.profile.ai_efficiency_score !== null 
                          ? devProfile.profile.ai_efficiency_score.toFixed(3) 
                          : 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Main Charts & Bug lists */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {/* Trend line chart */}
              <div className="glass-card">
                <h3 style={{ marginBottom: '16px' }}>Historical Trend Analysis</h3>
                {devProfile.history && devProfile.history.length < 2 ? (
                  <div style={{ height: '240px', display: 'flex', alignItems: 'center', justifySelf: 'center', color: 'var(--text-secondary)' }}>
                    Add at least 2 periods of historical data to render trend charts.
                  </div>
                ) : (
                  <div style={{ width: '100%', height: '260px' }}>
                    <ResponsiveContainer>
                      <LineChart data={devProfile.history} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="period" stroke="var(--text-secondary)" />
                        <YAxis yAxisId="left" stroke="var(--accent-primary)" />
                        <YAxis yAxisId="right" orientation="right" stroke="var(--flag-green)" />
                        <ChartTooltip 
                          contentStyle={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--card-border)' }} 
                          labelStyle={{ color: 'var(--text-primary)' }}
                        />
                        <Legend />
                        <Line yAxisId="left" type="monotone" dataKey="ai_efficiency_score" name="Efficiency Score (SP/$)" stroke="var(--accent-primary)" strokeWidth={2.5} activeDot={{ r: 6 }} />
                        <Line yAxisId="left" type="monotone" dataKey="spend_usd" name="Spend ($)" stroke="var(--accent-secondary)" strokeWidth={2} />
                        <Line yAxisId="right" type="monotone" dataKey="deliverables_count" name="Deliverables Count" stroke="var(--flag-green)" strokeWidth={2} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>

              {/* Attributed Bugs Detail List */}
              <div className="glass-card">
                <h3 style={{ marginBottom: '12px' }}>Attributed Bugs detail list — {selectedPeriod}</h3>
                {devProfile.bugs && devProfile.bugs.length === 0 ? (
                  <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '13px' }}>
                    No bugs attributed to this developer in this period.
                  </div>
                ) : (
                  <div className="table-container">
                    <table>
                      <thead>
                        <tr>
                          <th>Bug Key</th>
                          <th>Epic Link</th>
                          <th>Sprint</th>
                          <th>Bug Created</th>
                          <th>Story Resolved</th>
                          <th>Linked Story</th>
                        </tr>
                      </thead>
                      <tbody>
                        {devProfile.bugs && devProfile.bugs.map(b => (
                          <tr key={b.id}>
                            <td>
                              {jiraBaseUrl ? (
                                <a 
                                  href={`${jiraBaseUrl}${b.bug_key}`} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="table-link"
                                  style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                                >
                                  {b.bug_key} <ExternalLink size={12} />
                                </a>
                              ) : (
                                <strong>{b.bug_key}</strong>
                              )}
                            </td>
                            <td>{b.epic_key || '-'}</td>
                            <td>{b.sprint || '-'}</td>
                            <td>{b.created_date}</td>
                            <td>{b.resolved_date}</td>
                            <td>
                              {jiraBaseUrl && b.story_key ? (
                                <a 
                                  href={`${jiraBaseUrl}${b.story_key}`} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="table-link"
                                >
                                  {b.story_key}
                                </a>
                              ) : (
                                b.story_key || '-'
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 3. TEAM TRENDS VIEW */}
        {periods.length > 0 && currentView === 'trends' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            
            {/* Team trend KPI charts */}
            <div className="glass-card">
              <h2 style={{ marginBottom: '16px' }}>Team Productivity & Cost Trends</h2>
              {teamTrends.length < 2 ? (
                <div style={{ height: '240px', display: 'flex', alignItems: 'center', justifySelf: 'center', color: 'var(--text-secondary)' }}>
                  Add at least 2 periods of historical data to render team trend charts.
                </div>
              ) : (
                <div style={{ width: '100%', height: '300px' }}>
                  <ResponsiveContainer>
                    <LineChart data={teamTrends} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="period" stroke="var(--text-secondary)" />
                      <YAxis yAxisId="left" stroke="var(--accent-primary)" />
                      <YAxis yAxisId="right" orientation="right" stroke="var(--flag-green)" />
                      <ChartTooltip 
                        contentStyle={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--card-border)' }} 
                        labelStyle={{ color: 'var(--text-primary)' }}
                      />
                      <Legend />
                      <Line yAxisId="left" type="monotone" dataKey="total_spend" name="Total Spend ($)" stroke="var(--accent-primary)" strokeWidth={2.5} />
                      <Line yAxisId="right" type="monotone" dataKey="total_deliverables" name="Total Deliverables" stroke="var(--flag-green)" strokeWidth={2} />
                      <Line yAxisId="right" type="monotone" dataKey="total_bugs" name="Total Bugs" stroke="var(--flag-red)" strokeWidth={1.5} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              
              {/* Stacked Flag Distribution */}
              <div className="glass-card">
                <h3 style={{ marginBottom: '16px' }}>Developer Flag Distribution over Time</h3>
                {teamTrends.length === 0 ? (
                  <div style={{ height: '220px', display: 'flex', alignItems: 'center', justifySelf: 'center' }}>No historical data.</div>
                ) : (
                  <div style={{ width: '100%', height: '220px' }}>
                    <ResponsiveContainer>
                      <BarChart data={teamTrends.map(t => ({
                        period: t.period,
                        'On Track': t.flags.green,
                        'Quality Risk': t.flags.red,
                        'Coaching': t.flags.yellow,
                        'Needs Attention': t.flags.gray
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="period" stroke="var(--text-secondary)" />
                        <YAxis stroke="var(--text-secondary)" />
                        <ChartTooltip 
                          contentStyle={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--card-border)' }}
                        />
                        <Legend />
                        <Bar dataKey="On Track" stackId="a" fill="var(--flag-green)" />
                        <Bar dataKey="Quality Risk" stackId="a" fill="var(--flag-red)" />
                        <Bar dataKey="Coaching" stackId="a" fill="var(--flag-yellow)" />
                        <Bar dataKey="Needs Attention" stackId="a" fill="var(--flag-gray)" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>

              {/* AI Adoption Rate Card */}
              {teamTrends.length > 0 && (
                <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <h3 style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '6px' }}>AI Adoption Rate</h3>
                  {(() => {
                    const latestTrend = teamTrends[teamTrends.length - 1];
                    const rate = latestTrend.total_developers > 0 
                      ? ((latestTrend.active_developers / latestTrend.total_developers) * 100).toFixed(0)
                      : '0';

                    return (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', flexGrow: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                          <div style={{ 
                            fontSize: '48px', fontWeight: '700', fontFamily: 'var(--font-heading)',
                            color: rate === '100' ? 'var(--flag-green)' : 'var(--accent-primary)',
                            lineHeight: 1
                          }}>
                            {rate}%
                          </div>
                          <div>
                            <p style={{ fontWeight: '600', fontSize: '15px' }}>{latestTrend.active_developers} of {latestTrend.total_developers} developers</p>
                            <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>actively using Claude Code in latest period</p>
                          </div>
                        </div>

                        {/* List inactive developers */}
                        <div style={{ borderTop: '1px dashed var(--card-border)', paddingTop: '12px', flexGrow: 1 }}>
                          <span style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', display: 'block', marginBottom: '8px' }}>
                            Zero-Token Spend Developers ({latestTrend.total_developers - latestTrend.active_developers})
                          </span>
                          
                          {/* Fetch developers for the latest period and list those with spend == 0 */}
                          {leaderboardMetrics.filter(m => m.spend_usd === 0).length === 0 ? (
                            <p style={{ fontSize: '13px', color: 'var(--flag-green)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <Check size={14} /> All developers are actively using Claude Code!
                            </p>
                          ) : (
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', maxHeight: '100px', overflowY: 'auto' }}>
                              {leaderboardMetrics.filter(m => m.spend_usd === 0).map(m => (
                                <span 
                                  key={m.email}
                                  style={{ 
                                    background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239,68,68,0.2)',
                                    color: 'var(--flag-red)', padding: '4px 8px', borderRadius: '6px', fontSize: '11px' 
                                  }}
                                >
                                  {m.display_name}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })()}
                </div>
              )}
            </div>
          </div>
        )}

        {/* 4. ADMIN PANEL & DATA MANAGEMENT VIEW */}
        {currentView === 'admin' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            
            {/* Split row: File upload and Server dir run */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '24px' }}>
              
              {/* Web File Upload Ingestion */}
              <div className="glass-card">
                <h2 style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                  <Upload size={20} color="var(--accent-primary)" /> Manual CSV File Upload
                </h2>
                
                <form onSubmit={handleUploadSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div className="form-grid">
                    <div className="form-group">
                      <label>Period Format</label>
                      <div className="toggle-group" style={{ width: 'fit-content' }}>
                        <button 
                          type="button"
                          className={`toggle-btn ${uploadPeriodType === 'monthly' ? 'active' : ''}`}
                          onClick={() => setUploadPeriodType('monthly')}
                        >
                          Monthly
                        </button>
                        <button 
                          type="button"
                          className={`toggle-btn ${uploadPeriodType === 'weekly' ? 'active' : ''}`}
                          onClick={() => setUploadPeriodType('weekly')}
                        >
                          Weekly
                        </button>
                      </div>
                    </div>

                    <div className="form-group">
                      <label>{uploadPeriodType === 'monthly' ? 'Period (YYYY-MM)' : 'Period (YYYY-Www)'}</label>
                      <input 
                        type="text" 
                        placeholder={uploadPeriodType === 'monthly' ? 'e.g. 2026-05' : 'e.g. 2026-W23'} 
                        value={uploadPeriodValue}
                        onChange={(e) => setUploadPeriodValue(e.target.value)}
                        required
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label>1. Claude Console Usage export CSV</label>
                    <input 
                      type="file" 
                      accept=".csv"
                      onChange={(e) => setClaudeFile(e.target.files[0])}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>2. JIRA closed Stories/Tasks CSV</label>
                    <input 
                      type="file" 
                      accept=".csv"
                      onChange={(e) => setJiraDelivFile(e.target.files[0])}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>3. JIRA bugs CSV</label>
                    <input 
                      type="file" 
                      accept=".csv"
                      onChange={(e) => setJiraBugsFile(e.target.files[0])}
                      required
                    />
                  </div>

                  <button className="btn" type="submit" disabled={isUploading}>
                    {isUploading ? (
                      <>
                        <span className="spinner" style={{ width: '16px', height: '16px' }}></span> Ingesting...
                      </>
                    ) : (
                      <>
                        <Upload size={16} /> Run & Ingest CSVs
                      </>
                    )}
                  </button>
                </form>
              </div>

              {/* Server Folder Ingestion trigger */}
              <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <h2 style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Database size={20} color="var(--accent-primary)" /> Server Files Ingestion
                </h2>
                
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                  Trigger pipeline on files already placed in the server's directory <code>./data_drop/</code>. Ensure files are named exactly: 
                  <code style={{ display: 'block', margin: '4px 0', fontSize: '11px' }}>claude_export.csv</code>
                  <code style={{ display: 'block', margin: '4px 0', fontSize: '11px' }}>jira_deliverables.csv</code>
                  <code style={{ display: 'block', margin: '4px 0', fontSize: '11px' }}>jira_bugs.csv</code>
                </p>

                <form onSubmit={handleServerRun} style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: 'auto' }}>
                  <div className="form-group">
                    <label>Target Period (YYYY-MM or YYYY-Www)</label>
                    <input 
                      type="text" 
                      placeholder="e.g. 2026-05" 
                      value={serverPeriodValue}
                      onChange={(e) => setServerPeriodValue(e.target.value)}
                      required
                    />
                  </div>

                  <button className="btn btn-secondary" type="submit" disabled={isServerRunning}>
                    {isServerRunning ? (
                      <>
                        <span className="spinner" style={{ width: '16px', height: '16px' }}></span> Executing...
                      </>
                    ) : (
                      <>
                        <Database size={16} /> Run Pipeline from Server
                      </>
                    )}
                  </button>
                </form>
              </div>

            </div>

            {/* Config & Developer map edit row */}
            <div style={{ display: 'grid', gridTemplateColumns: '0.8fr 1.2fr', gap: '24px' }}>
              
              {/* Jira Base URL setting */}
              <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <h2>JIRA Base Link Configurations</h2>
                <form onSubmit={saveJiraConfig} style={{ display: 'flex', flexDirection: 'column', gap: '12px', flexGrow: 1 }}>
                  <div className="form-group" style={{ flexGrow: 1 }}>
                    <label>Jira Base Prefix URL</label>
                    <input 
                      type="text" 
                      placeholder="e.g. https://mycompany.atlassian.net/browse/" 
                      value={jiraBaseUrl}
                      onChange={(e) => setJiraBaseUrl(e.target.value)}
                    />
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                      Keys on profile lists (e.g. BUG-201) will hyperlink to JIRA if configured.
                    </span>
                  </div>
                  <button className="btn" type="submit" style={{ marginTop: 'auto' }}>
                    Save Configurations
                  </button>
                </form>
              </div>

              {/* Developer email mapping editor */}
              <div className="glass-card">
                <h2>Developer Name-to-Email mappings</h2>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                  Map JIRA assignee display names to Claude Console emails (both lowercased inside loader).
                </p>

                {/* Add new row form */}
                <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                  <input 
                    type="text" 
                    placeholder="Display Name (e.g. Navneet Shukla)" 
                    value={newDevName}
                    onChange={(e) => setNewDevName(e.target.value)}
                    style={{ flexGrow: 1 }}
                  />
                  <input 
                    type="text" 
                    placeholder="Email (e.g. navneet.shukla@cashflo.io)" 
                    value={newDevEmail}
                    onChange={(e) => setNewDevEmail(e.target.value)}
                    style={{ flexGrow: 1 }}
                  />
                  <button className="btn" type="button" onClick={addDeveloperToMap}>
                    <Plus size={16} /> Add
                  </button>
                </div>

                <div className="table-container" style={{ maxHeight: '160px', overflowY: 'auto', border: '1px solid var(--card-border)', borderRadius: '8px' }}>
                  <table>
                    <thead>
                      <tr style={{ background: 'rgba(255,255,255,0.02)' }}>
                        <th>Jira Display Name</th>
                        <th>Mapped Email</th>
                        <th style={{ width: '60px', textAlign: 'center' }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {developersMap.length === 0 ? (
                        <tr>
                          <td colSpan="3" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                            No developer mappings set. Add one above.
                          </td>
                        </tr>
                      ) : (
                        developersMap.map((dev, idx) => (
                          <tr key={idx}>
                            <td>{dev.display_name}</td>
                            <td>{dev.email}</td>
                            <td style={{ textAlign: 'center' }}>
                              <button 
                                type="button" 
                                style={{ background: 'transparent', border: 'none', color: 'var(--flag-red)', cursor: 'pointer' }}
                                onClick={() => removeDeveloperFromMap(idx)}
                              >
                                <Trash size={14} />
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                <button 
                  className="btn" 
                  type="button" 
                  onClick={saveDevelopersMap}
                  style={{ marginTop: '16px', width: '100%' }}
                >
                  Save Developer Mappings List
                </button>
              </div>

            </div>

            {/* Run logs list */}
            <div className="glass-card">
              <h2 style={{ marginBottom: '12px' }}>Upload & Ingestion run log (Last 20)</h2>
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>Period</th>
                      <th>Trigger Type</th>
                      <th>Ingestion Status</th>
                      <th>Details / Failure Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runs.length === 0 ? (
                      <tr>
                        <td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No runs logged yet.</td>
                      </tr>
                    ) : (
                      runs.map(run => (
                        <tr key={run.id}>
                          <td style={{ color: 'var(--text-secondary)' }}>
                            {new Date(run.timestamp).toLocaleString()}
                          </td>
                          <td style={{ fontWeight: '500' }}>{run.period}</td>
                          <td>
                            <code style={{ fontSize: '11px' }}>{run.trigger_type}</code>
                          </td>
                          <td>
                            <span className={`badge ${run.status === 'success' ? 'badge-green' : 'badge-red'}`}>
                              {run.status}
                            </span>
                          </td>
                          <td style={{ color: run.status === 'failed' ? 'var(--flag-red)' : 'var(--text-secondary)', fontSize: '12px' }}>
                            {run.error_message || 'Completed successfully.'}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        )}

      </main>

      <footer style={{ marginTop: 'auto', padding: '24px 0', borderTop: '1px solid rgba(255,255,255,0.05)', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>
        <p>Cashflo Engineering — AI Developer Productivity Dashboard Web App MVP — 2026</p>
      </footer>
    </div>
  );
}
