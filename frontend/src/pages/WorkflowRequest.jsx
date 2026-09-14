import React, { useState } from 'react';
import { Terminal, Send, Sparkles, AlertCircle, CheckCircle2, User, Calendar, UserCheck } from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';
import { apiService } from '../services/api';

export function WorkflowRequestPage({ onExecuteWorkflow }) {
  const [query, setQuery] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  const sampleQueries = [
    "I need an appointment with a cardiologist tomorrow.",
    "Find an available neurologist.",
    "Show appointments for patient P001.",
    "Find an available doctor.",
    "Book an appointment."
  ];

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim() || isProcessing) return;

    setIsProcessing(true);
    setError(null);

    try {
      const res = await apiService.sendWorkflowRequest(query.trim());
      setResponse(res);
      if (onExecuteWorkflow) {
        onExecuteWorkflow(res);
      }
    } catch (err) {
      setError(err.message || "Failed to process workflow request.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSampleClick = (text) => {
    setQuery(text);
  };

  const parsed = response?.parsed_request;
  const resultData = response?.data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-dark-800 border border-dark-700/80 p-6 rounded-2xl shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-cyan-500/10 text-cyan-400 rounded-xl border border-cyan-500/20">
            <Terminal className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">AI Workflow Command Terminal</h1>
            <p className="text-xs text-gray-400 mt-1">Submit natural-language hospital requests to be parsed by LLM and processed by AI Agents.</p>
          </div>
        </div>
      </div>

      {/* Input Query Form */}
      <div className="bg-dark-800 border border-dark-700/80 rounded-2xl p-6 shadow-xl space-y-4">
        <form onSubmit={handleSubmit} className="space-y-3">
          <label className="block text-xs font-mono text-gray-300 uppercase tracking-wider">
            OPERATIONAL REQUEST INPUT
          </label>
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. 'I need an appointment with a cardiologist tomorrow' or 'Find available neurologist'..."
              className="w-full bg-dark-900 border border-dark-600 rounded-xl px-4 py-3.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition-colors pr-32 font-sans"
            />
            <button
              type="submit"
              disabled={isProcessing || !query.trim()}
              className="absolute right-2 top-2 bottom-2 px-4 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-medium text-xs rounded-lg flex items-center gap-1.5 shadow-md disabled:opacity-50 transition-all"
            >
              {isProcessing ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Parsing...</span>
                </>
              ) : (
                <>
                  <span>Process</span>
                  <Send className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </form>

        {/* Sample Prompt Chips */}
        <div>
          <span className="text-[11px] font-mono text-gray-500 block mb-2">QUICK TEST PROMPTS:</span>
          <div className="flex flex-wrap gap-2">
            {sampleQueries.map((sample, idx) => (
              <button
                key={idx}
                onClick={() => handleSampleClick(sample)}
                className="px-3 py-1.5 rounded-lg bg-dark-900 hover:bg-dark-700 text-gray-300 border border-dark-700 text-xs font-sans transition-colors flex items-center gap-1.5"
              >
                <Sparkles className="w-3 h-3 text-cyan-400" />
                <span>{sample}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Response Panel */}
      {response && (
        <div className="space-y-6 animate-fadeIn">
          {/* Top Status Bar */}
          <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-5 shadow-lg flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
            <div>
              <span className="text-[10px] font-mono text-gray-500 uppercase tracking-widest block">EXECUTED WORKFLOW</span>
              <h3 className="font-bold text-white text-base mt-0.5">"{response.original_request}"</h3>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono text-cyan-400 bg-cyan-500/10 px-3 py-1 rounded-lg border border-cyan-500/20">
                Agent: {response.agent_used}
              </span>
              <StatusBadge status={response.status} />
            </div>
          </div>

          {/* Grid: Parsed Request Parameters & Agent Steps */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Parsed JSON Parameters */}
            <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-5 shadow-lg space-y-3">
              <h4 className="font-bold text-sm text-white pb-2 border-b border-dark-700 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                <span>Structured LLM Request Parsing</span>
              </h4>

              {parsed && (
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="p-2.5 bg-dark-900 rounded-lg border border-dark-700">
                    <span className="text-gray-500 block text-[10px]">REQUEST TYPE</span>
                    <span className="font-semibold text-cyan-400">{parsed.request_type}</span>
                  </div>
                  <div className="p-2.5 bg-dark-900 rounded-lg border border-dark-700">
                    <span className="text-gray-500 block text-[10px]">URGENCY</span>
                    <span className="font-semibold text-emerald-400">{parsed.urgency}</span>
                  </div>
                  <div className="p-2.5 bg-dark-900 rounded-lg border border-dark-700">
                    <span className="text-gray-500 block text-[10px]">DEPARTMENT / SPEC</span>
                    <span className="font-semibold text-white">{parsed.department || 'N/A'}</span>
                  </div>
                  <div className="p-2.5 bg-dark-900 rounded-lg border border-dark-700">
                    <span className="text-gray-500 block text-[10px]">PATIENT / DOCTOR ID</span>
                    <span className="font-semibold text-white">{parsed.patient_id || parsed.doctor_id || 'N/A'}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Agent Steps Timeline */}
            <div className="bg-dark-800 border border-dark-700/80 rounded-xl p-5 shadow-lg space-y-3">
              <h4 className="font-bold text-sm text-white pb-2 border-b border-dark-700 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Agent Tool Execution Steps</span>
              </h4>

              <div className="space-y-2 font-mono text-xs">
                {response.steps?.map((step, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-gray-300 p-2 bg-dark-900/60 rounded-lg border border-dark-700/50">
                    <span className="text-cyan-400 font-bold">&gt;</span>
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Database Recommendation Banner */}
          <div className="bg-dark-800 border border-dark-700/80 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-wider">
              <Sparkles className="w-4 h-4" />
              <span>DATABASE-BACKED AGENT RECOMMENDATION</span>
            </div>

            <div className="p-4 bg-cyan-500/10 border border-cyan-500/20 rounded-xl text-sm font-medium text-white leading-relaxed">
              {response.recommendation}
            </div>

            {/* Render Detailed Result Cards if available */}
            {resultData?.doctors && (
              <div className="space-y-3 pt-2">
                <h5 className="text-xs font-mono text-gray-400 uppercase">Matching Doctor Records:</h5>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {resultData.doctors.map((doc, idx) => (
                    <div key={idx} className="p-3 bg-dark-900 rounded-lg border border-dark-700 text-xs flex justify-between items-center">
                      <div>
                        <div className="font-semibold text-white">{doc.name} ({doc.doctor_id})</div>
                        <div className="text-[11px] text-gray-400">{doc.specialization} | Shift: {doc.shift}</div>
                      </div>
                      <StatusBadge status={doc.availability ? 'available' : 'unavailable'} />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {resultData?.patient && (
              <div className="p-4 bg-dark-900 rounded-xl border border-dark-700 text-xs space-y-2">
                <div className="font-bold text-white text-sm flex items-center gap-2">
                  <User className="w-4 h-4 text-cyan-400" />
                  <span>Patient Record: {resultData.patient.name} ({resultData.patient.patient_id})</span>
                </div>
                <div className="text-gray-400">
                  Age: {resultData.patient.age} yrs | Gender: {resultData.patient.gender} | Dept: {resultData.patient.department} | Blood Group: {resultData.patient.blood_group}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
