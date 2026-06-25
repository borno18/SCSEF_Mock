import React, { useState, useEffect, useRef } from 'react';
import { ShieldAlert, Activity, CheckCircle, AlertTriangle, Send, History, Cpu, Sparkles } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function App() {
  const [ticketId, setTicketId] = useState('');
  const [channel, setChannel] = useState('app');
  const [locale, setLocale] = useState('en');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [warnTimeout, setWarnTimeout] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [healthStatus, setHealthStatus] = useState('unknown'); // 'ok', 'degraded', 'unknown'
  
  const timerRef = useRef(null);

  // Generate default ticket_id
  const generateTicketId = () => {
    return `T-${Date.now()}`;
  };

  useEffect(() => {
    setTicketId(generateTicketId());
    
    // Check health initially and every 15 seconds
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'ok') {
          setHealthStatus('ok');
        } else {
          setHealthStatus('degraded');
        }
      } else {
        setHealthStatus('degraded');
      }
    } catch (e) {
      setHealthStatus('degraded');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) {
      setErrorMsg('Message field is required.');
      return;
    }

    setLoading(true);
    setWarnTimeout(false);
    setErrorMsg('');
    setResult(null);

    // Setup a timer to alert the user if requests are slow (>10 seconds)
    timerRef.current = setTimeout(() => {
      setWarnTimeout(true);
    }, 10000);

    const payload = {
      ticket_id: ticketId,
      channel,
      locale,
      message,
    };

    try {
      const response = await fetch(`${API_BASE_URL}/sort-ticket`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      clearTimeout(timerRef.current);

      if (response.ok) {
        const data = await response.json();
        setResult(data);
        // Append to local history list (up to 10 latest entries)
        setHistory((prev) => [data, ...prev.slice(0, 9)]);
        // Regenerate ticket_id for next entry
        setTicketId(generateTicketId());
        setMessage('');
      } else {
        const errText = await response.text();
        setErrorMsg(`Error [${response.status}]: ${errText || 'Failed to sort ticket'}`);
      }
    } catch (err) {
      clearTimeout(timerRef.current);
      setErrorMsg(`Network Error: Make sure backend is running at ${API_BASE_URL}`);
    } finally {
      setLoading(false);
    }
  };

  // Helper for colored pill classes based on severity
  const getSeverityPill = (severity) => {
    const s = severity.toLowerCase();
    if (s === 'low') return 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20';
    if (s === 'medium') return 'bg-amber-500/10 text-amber-400 border border-amber-500/20';
    if (s === 'high') return 'bg-orange-500/10 text-orange-400 border border-orange-500/20';
    return 'bg-rose-500/10 text-rose-400 border border-rose-500/20 animate-pulse';
  };

  // Helper for case_type colored badges
  const getCaseTypeBadge = (caseType) => {
    const c = caseType.toLowerCase();
    if (c === 'wrong_transfer') return 'bg-blue-500/10 text-blue-400 border border-blue-500/20';
    if (c === 'payment_failed') return 'bg-purple-500/10 text-purple-400 border border-purple-500/20';
    if (c === 'refund_request') return 'bg-sky-500/10 text-sky-400 border border-sky-500/20';
    if (c === 'phishing_or_social_engineering') return 'bg-red-500/10 text-red-400 border border-red-500/20 font-semibold';
    return 'bg-slate-500/10 text-slate-400 border border-slate-500/20';
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center py-10 px-4 md:px-8 font-sans selection:bg-teal-500 selection:text-slate-950">
      
      {/* Top Banner & Health check indicator */}
      <div className="w-full max-w-6xl flex justify-between items-center mb-8 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <Cpu className="w-8 h-8 text-teal-400 animate-spin-slow" />
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight bg-gradient-to-r from-teal-400 via-emerald-400 to-indigo-400 bg-clip-text text-transparent">
            QueueStorm Dashboard
          </h1>
        </div>
        <div className="flex items-center gap-2 bg-slate-900/60 backdrop-blur-md px-3 py-1.5 rounded-full border border-slate-800">
          <Activity className="w-4 h-4 text-slate-400" />
          <span className="text-xs text-slate-400 font-medium">Service Health:</span>
          <span className={`inline-block w-2.5 h-2.5 rounded-full ${healthStatus === 'ok' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            {healthStatus === 'ok' ? 'Online' : 'Degraded'}
          </span>
        </div>
      </div>

      <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Triaging Form Column */}
        <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 rounded-2xl p-6 md:p-8 shadow-2xl flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-teal-400" />
              <h2 className="text-lg font-bold text-slate-200">Submit Customer Ticket</h2>
            </div>
            
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">Ticket ID</label>
                  <input
                    type="text"
                    value={ticketId}
                    onChange={(e) => setTicketId(e.target.value)}
                    required
                    className="w-full bg-slate-950/80 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-teal-500 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">Locale</label>
                  <select
                    value={locale}
                    onChange={(e) => setLocale(e.target.value)}
                    className="w-full bg-slate-950/80 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-teal-500 transition-colors"
                  >
                    <option value="en">English (en)</option>
                    <option value="bn">Bengali (bn)</option>
                    <option value="mixed">Mixed (bn / en)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">Channel</label>
                <select
                  value={channel}
                  onChange={(e) => setChannel(e.target.value)}
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-teal-500 transition-colors"
                >
                  <option value="app">App Portal</option>
                  <option value="sms">SMS Client</option>
                  <option value="call_center">Call Center Dispatch</option>
                  <option value="merchant_portal">Merchant Portal</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">Customer Message</label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Enter user query..."
                  rows="5"
                  required
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-teal-500 transition-colors placeholder:text-slate-700"
                />
              </div>

              {errorMsg && (
                <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 p-3 rounded-lg text-sm flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 flex-shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}

              {warnTimeout && (
                <div className="bg-amber-500/10 border border-amber-500/20 text-amber-400 p-3 rounded-lg text-xs flex items-center gap-2 animate-pulse">
                  <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                  <span>The backend is taking longer than expected. Please continue waiting (budget is up to 30s).</span>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-400 hover:to-emerald-500 disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-500 text-slate-950 font-bold py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-teal-500/20 cursor-pointer disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-slate-950" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Triaging Ticket...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    <span>Run Sort Triage</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Sorting Results Column */}
        <div className="space-y-6">
          {/* Classification output details */}
          <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 rounded-2xl p-6 md:p-8 shadow-2xl min-h-[300px] flex flex-col justify-between">
            {result ? (
              <div className="space-y-6">
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-widest">Triage Result</span>
                    <h3 className="text-xl font-black text-slate-100 mt-1">{result.ticket_id}</h3>
                  </div>
                  <span className={`px-2.5 py-1 text-xs font-bold rounded-full uppercase tracking-wider ${getSeverityPill(result.severity)}`}>
                    {result.severity}
                  </span>
                </div>

                {result.human_review_required && (
                  <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 py-2.5 px-4 rounded-xl flex items-center gap-2">
                    <ShieldAlert className="w-5 h-5 flex-shrink-0 animate-bounce" />
                    <span className="text-xs font-bold uppercase tracking-wider">⚠ Needs Human Review Queue Escalation</span>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800">
                    <span className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Case Type</span>
                    <span className={`inline-block px-2.5 py-0.5 rounded text-xs uppercase tracking-wide ${getCaseTypeBadge(result.case_type)}`}>
                      {result.case_type.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800">
                    <span className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Target Department</span>
                    <span className="inline-block px-2.5 py-0.5 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded text-xs uppercase tracking-wide font-medium">
                      {result.department.replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>

                <div className="space-y-2">
                  <span className="block text-xs font-bold uppercase tracking-wider text-slate-500">Agent Summary</span>
                  <p className="bg-slate-950/40 p-4 rounded-xl border border-slate-800 text-sm leading-relaxed text-slate-200">
                    {result.agent_summary}
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between items-center text-xs text-slate-400 font-medium">
                    <span>Triage Confidence</span>
                    <span className="font-bold text-slate-200">{Math.round(result.confidence * 100)}%</span>
                  </div>
                  <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                    <div
                      className="bg-gradient-to-r from-teal-500 to-indigo-500 h-full rounded-full transition-all duration-500"
                      style={{ width: `${result.confidence * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-20 text-slate-600 gap-3">
                <Cpu className="w-12 h-12 text-slate-800 stroke-[1.5]" />
                <p className="text-sm font-medium">Submit a support ticket to verify classification metrics.</p>
              </div>
            )}
          </div>

          {/* Session Triage History list */}
          <div className="bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 rounded-2xl p-6 shadow-2xl">
            <div className="flex items-center gap-2 mb-4 pb-2 border-b border-slate-800/50">
              <History className="w-4 h-4 text-slate-400" />
              <h3 className="text-sm font-bold text-slate-300">Session History (Max 10)</h3>
            </div>
            
            {history.length > 0 ? (
              <div className="space-y-3 max-h-[240px] overflow-y-auto pr-1">
                {history.map((item, idx) => (
                  <div key={idx} className="bg-slate-950/60 p-3 rounded-xl border border-slate-850 flex items-center justify-between gap-4 text-xs">
                    <div className="flex flex-col gap-1 min-w-0">
                      <span className="font-bold text-slate-300 truncate">{item.ticket_id}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-500 font-medium uppercase tracking-wider">{item.department.replace(/_/g, ' ')}</span>
                        <span className="text-slate-600">•</span>
                        <span className="text-slate-400 line-clamp-1">{item.agent_summary}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider ${getSeverityPill(item.severity)}`}>
                        {item.severity}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-600 text-center py-4">No sorted tickets in current session.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
