import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Search,
  Upload,
  FileText,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Trash2,
  ShieldAlert,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Database,
  Layers
} from 'lucide-react';
import { apiService } from '../services/api';

export function PoliciesPage() {
  const [activeTab, setActiveTab] = useState('assistant'); // 'assistant' | 'documents' | 'upload'
  const [policies, setPolicies] = useState([]);
  const [selectedDept, setSelectedDept] = useState('All');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Policy Assistant State
  const [query, setQuery] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [answerData, setAnswerData] = useState(null);

  // Selected document chunks modal
  const [selectedDocChunks, setSelectedDocChunks] = useState(null);
  const [chunksLoading, setChunksLoading] = useState(false);

  // Upload Form State
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadDept, setUploadDept] = useState('General');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);

  // Get current user role
  const currentUserRole = localStorage.getItem('cc_role') || 'ADMIN';

  const fetchPolicies = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiService.getPolicies(selectedDept === 'All' ? null : selectedDept);
      setPolicies(data);
    } catch (err) {
      setError(err.message || 'Failed to fetch policy documents.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, [selectedDept]);

  const handleAsk = async (e, customQuery = null) => {
    if (e) e.preventDefault();
    const q = customQuery || query;
    if (!q.trim()) return;

    setIsAsking(true);
    setError(null);
    try {
      const res = await apiService.askPolicy({
        query: q,
        department: selectedDept !== 'All' ? selectedDept : null,
        top_k: 4
      });
      setAnswerData(res);
      setQuery(q);
    } catch (err) {
      setError(err.message || 'Failed to query policy intelligence assistant.');
    } finally {
      setIsAsking(false);
    }
  };

  const handleViewChunks = async (doc) => {
    setChunksLoading(true);
    try {
      const chunks = await apiService.getPolicyChunks(doc.document_id);
      setSelectedDocChunks({ doc, chunks });
    } catch (err) {
      alert('Failed to load chunks: ' + err.message);
    } finally {
      setChunksLoading(false);
    }
  };

  const handleDeletePolicy = async (documentId) => {
    if (!window.confirm('Are you sure you want to delete this policy and remove all embeddings from the vector store?')) return;
    try {
      await apiService.deletePolicy(documentId);
      await fetchPolicies();
      if (selectedDocChunks && selectedDocChunks.doc.document_id === documentId) {
        setSelectedDocChunks(null);
      }
    } catch (err) {
      alert('Delete failed: ' + err.message);
    }
  };

  const handleReprocessPolicy = async (documentId) => {
    try {
      await apiService.reprocessPolicy(documentId);
      await fetchPolicies();
      alert('Document re-indexed and vector store updated successfully.');
    } catch (err) {
      alert('Reprocess failed: ' + err.message);
    }
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!uploadFile) {
      alert('Please select a PDF, DOCX, or TXT file.');
      return;
    }

    setIsUploading(true);
    setUploadSuccess(null);
    setError(null);

    const formData = new FormData();
    formData.append('file', uploadFile);
    if (uploadTitle) formData.append('title', uploadTitle);
    formData.append('department', uploadDept);

    try {
      const res = await apiService.uploadPolicy(formData);
      setUploadSuccess(`Successfully ingested "${res.title}" with ${res.chunk_count} chunk(s) indexed into ChromaDB!`);
      setUploadFile(null);
      setUploadTitle('');
      await fetchPolicies();
    } catch (err) {
      setError(err.message || 'Failed to upload and ingest document.');
    } finally {
      setIsUploading(false);
    }
  };

  const PRESET_QUERIES = [
    "What are the visiting hours for the Intensive Care Unit (ICU)?",
    "How much advance notice is required to cancel a general outpatient consultation?",
    "What is the bed turnaround time for isolation rooms including UV-C disinfection?",
    "By what time should scheduled patients vacate their beds on discharge day?",
    "What is the protocol for identifying unconscious unidentified trauma patients?"
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gray-900 border border-gray-800 p-6 rounded-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl -z-10"></div>
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 flex items-center gap-1.5">
              <Sparkles className="w-3 h-3 text-cyan-400" /> Phase 5 RAG Intelligence
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
              <Database className="w-3 h-3 text-emerald-400" /> ChromaDB Local Vector Store
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <BookOpen className="w-7 h-7 text-cyan-400" /> Hospital Policy Intelligence
          </h1>
          <p className="text-sm text-gray-400 mt-1 max-w-2xl">
            Semantic retrieval-augmented question answering grounded strictly in verified hospital administration protocols, bed utilization, and emergency workflows.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex bg-gray-800/80 p-1.5 rounded-xl border border-gray-700/60 self-start md:self-auto">
          <button
            onClick={() => setActiveTab('assistant')}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
              activeTab === 'assistant'
                ? 'bg-cyan-500 text-black shadow-lg shadow-cyan-500/20 font-semibold'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Sparkles className="w-4 h-4" /> Policy Assistant
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
              activeTab === 'documents'
                ? 'bg-cyan-500 text-black shadow-lg shadow-cyan-500/20 font-semibold'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <FileText className="w-4 h-4" /> Knowledge Base ({policies.length})
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
              activeTab === 'upload'
                ? 'bg-cyan-500 text-black shadow-lg shadow-cyan-500/20 font-semibold'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Upload className="w-4 h-4" /> Upload Document
          </button>
        </div>
      </div>

      {/* Global Error Banner */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-sm text-rose-400 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* TAB 1: POLICY ASSISTANT */}
      {activeTab === 'assistant' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Query & Presets Column */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-4">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400 flex items-center gap-2">
                <Search className="w-4 h-4 text-cyan-400" /> Ask Policy Question
              </h2>

              <form onSubmit={handleAsk} className="space-y-3">
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask any question regarding hospital policies, visiting hours, admission, bed guidelines..."
                  rows={3}
                  className="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 resize-none"
                />

                <div className="flex items-center gap-2">
                  <select
                    value={selectedDept}
                    onChange={(e) => setSelectedDept(e.target.value)}
                    className="bg-gray-950 border border-gray-800 rounded-xl px-3 py-2 text-xs text-gray-300 focus:outline-none focus:border-cyan-500 flex-1"
                  >
                    <option value="All">All Departments</option>
                    <option value="Hospital Administration">Hospital Administration</option>
                    <option value="Outpatient Services">Outpatient Services</option>
                    <option value="Bed Management">Bed Management</option>
                    <option value="Emergency Medicine">Emergency Medicine</option>
                    <option value="Patient Admissions">Patient Admissions</option>
                    <option value="Clinical Quality">Clinical Quality</option>
                  </select>

                  <button
                    type="submit"
                    disabled={isAsking || !query.trim()}
                    className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 text-black font-semibold text-xs rounded-xl shadow-lg shadow-cyan-500/20 hover:opacity-95 transition-all flex items-center gap-1.5 disabled:opacity-50"
                  >
                    {isAsking ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Retrieving...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5" /> Ask AI
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>

            {/* Quick Preset Questions */}
            <div className="bg-gray-900 border border-gray-800 rounded-2xl p-5 space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                Frequently Asked Policy Topics
              </h3>
              <div className="space-y-2">
                {PRESET_QUERIES.map((pq, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleAsk(null, pq)}
                    disabled={isAsking}
                    className="w-full text-left p-2.5 rounded-xl bg-gray-950/60 hover:bg-gray-800 border border-gray-800/80 text-xs text-gray-300 transition-colors flex items-center justify-between group"
                  >
                    <span className="line-clamp-2">{pq}</span>
                    <ChevronRight className="w-3.5 h-3.5 text-gray-500 group-hover:text-cyan-400 group-hover:translate-x-0.5 transition-all flex-shrink-0 ml-2" />
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Answer & Sources Column */}
          <div className="lg:col-span-2 space-y-6">
            {isAsking && (
              <div className="bg-gray-900 border border-gray-800 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-3">
                <div className="w-10 h-10 border-3 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
                <p className="text-sm text-cyan-400 font-medium">Executing ChromaDB Semantic Retrieval & Grounding...</p>
                <p className="text-xs text-gray-500">Searching 384-dimensional vector embeddings with anti-hallucination check</p>
              </div>
            )}

            {!isAsking && !answerData && (
              <div className="bg-gray-900 border border-gray-800 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-4">
                <div className="p-4 bg-cyan-500/10 rounded-2xl border border-cyan-500/20 text-cyan-400">
                  <BookOpen className="w-10 h-10" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Ask a Hospital Policy Question</h3>
                  <p className="text-xs text-gray-400 mt-1 max-w-md mx-auto">
                    Select a preset topic from the left or type any operational inquiry. Answers are synthesized exclusively from official hospital documents.
                  </p>
                </div>
              </div>
            )}

            {!isAsking && answerData && (
              <div className="space-y-6">
                {/* Main Grounded Answer Card */}
                <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-4 relative overflow-hidden">
                  <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-gray-800">
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5" /> Grounded RAG Answer
                      </span>
                      {answerData.insufficient_information ? (
                        <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3" /> Insufficient Information
                        </span>
                      ) : (
                        <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" /> High Confidence ({Math.round(answerData.confidence_score * 100)}%)
                        </span>
                      )}
                    </div>
                    <span className="text-xs font-mono text-gray-400">
                      ⚡ Latency: {answerData.execution_time_ms} ms
                    </span>
                  </div>

                  {/* Question */}
                  <div>
                    <span className="text-xs font-mono text-gray-400 uppercase tracking-wider">Inquiry</span>
                    <h3 className="text-base font-medium text-white mt-0.5">{answerData.query}</h3>
                  </div>

                  {/* Answer Body */}
                  <div className="p-4 bg-gray-950/70 border border-gray-800/80 rounded-xl">
                    <p className="text-sm text-gray-200 whitespace-pre-line leading-relaxed">
                      {answerData.answer}
                    </p>
                  </div>

                  {/* Anti-Hallucination Disclaimer */}
                  <div className="p-3 bg-blue-500/5 border border-blue-500/20 rounded-xl flex items-start gap-2.5">
                    <ShieldAlert className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                    <span className="text-xs text-blue-300/80 leading-normal">
                      <strong>Operational Policy Notice:</strong> This intelligence service strictly references verified hospital operational procedures. It is not intended for medical diagnoses, clinical treatment protocols, or drug prescriptions.
                    </span>
                  </div>
                </div>

                {/* Sources & Citations Section */}
                <div className="space-y-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 flex items-center justify-between">
                    <span>Retrieved Knowledge Chunks ({answerData.sources.length})</span>
                    <span className="text-gray-400 font-normal">ChromaDB Top Matches</span>
                  </h3>

                  {answerData.sources.length === 0 ? (
                    <div className="p-4 bg-gray-900 border border-gray-800 rounded-xl text-center text-xs text-gray-500">
                      No matching document chunks met the relevance threshold.
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {answerData.sources.map((src, i) => (
                        <div
                          key={i}
                          className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-2 hover:border-gray-700 transition-all flex flex-col justify-between"
                        >
                          <div>
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="px-2 py-0.5 rounded bg-gray-800 text-cyan-400 font-medium">
                                {src.department}
                              </span>
                              <span className="text-emerald-400 font-mono text-[11px]">
                                {Math.round(src.similarity_score * 100)}% match
                              </span>
                            </div>
                            <h4 className="text-sm font-semibold text-white line-clamp-1">{src.document_name}</h4>
                            <p className="text-xs text-gray-400 italic line-clamp-3 mt-1.5 bg-gray-950 p-2.5 rounded-lg border border-gray-800/60 font-sans">
                              "{src.content_snippet}"
                            </p>
                          </div>
                          <div className="pt-2 border-t border-gray-800/60 flex items-center justify-between text-[11px] text-gray-400 font-mono">
                            <span>Page {src.page_number || 1} • Chunk #{src.chunk_index + 1}</span>
                            <span className="text-gray-400">{src.document_id}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: KNOWLEDGE BASE (DOCUMENT LIST) */}
      {activeTab === 'documents' && (
        <div className="space-y-6">
          {/* Department Filter & Stats */}
          <div className="flex flex-wrap items-center justify-between gap-4 bg-gray-900 border border-gray-800 p-4 rounded-xl">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400 uppercase font-semibold">Filter Department:</span>
              <select
                value={selectedDept}
                onChange={(e) => setSelectedDept(e.target.value)}
                className="bg-gray-950 border border-gray-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
              >
                <option value="All">All Departments</option>
                <option value="Hospital Administration">Hospital Administration</option>
                <option value="Outpatient Services">Outpatient Services</option>
                <option value="Bed Management">Bed Management</option>
                <option value="Emergency Medicine">Emergency Medicine</option>
                <option value="Patient Admissions">Patient Admissions</option>
                <option value="Clinical Quality">Clinical Quality</option>
              </select>
            </div>

            <div className="flex items-center gap-4 text-xs font-mono text-gray-400">
              <span>Total Documents: <strong className="text-white">{policies.length}</strong></span>
              <span>Total Chunks: <strong className="text-cyan-400">{policies.reduce((acc, p) => acc + p.chunk_count, 0)}</strong></span>
            </div>
          </div>

          {/* Documents Table */}
          <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-gray-800 bg-gray-950/60 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    <th className="py-3 px-4">Document Title</th>
                    <th className="py-3 px-4">Department</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Chunks</th>
                    <th className="py-3 px-4">Size</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800 text-xs text-gray-300">
                  {policies.map((doc) => (
                    <tr key={doc.document_id} className="hover:bg-gray-800/40 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="font-medium text-white">{doc.title}</div>
                        <div className="text-[11px] text-gray-400 font-mono">{doc.filename}</div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="px-2 py-0.5 rounded bg-gray-800 text-gray-300">
                          {doc.department}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-mono uppercase">{doc.file_type}</td>
                      <td className="py-3.5 px-4 font-mono text-cyan-400">{doc.chunk_count}</td>
                      <td className="py-3.5 px-4 font-mono text-gray-400">
                        {Math.round(doc.file_size_bytes / 1024)} KB
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                          doc.status === 'INDEXED'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                        }`}>
                          {doc.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right space-x-2">
                        <button
                          onClick={() => handleViewChunks(doc)}
                          className="px-2.5 py-1 bg-gray-800 hover:bg-gray-700 text-cyan-400 rounded-lg text-xs font-medium transition-colors"
                        >
                          View Chunks
                        </button>
                        {currentUserRole === 'ADMIN' && (
                          <>
                            <button
                              onClick={() => handleReprocessPolicy(doc.document_id)}
                              title="Re-index into ChromaDB"
                              className="p-1 hover:text-cyan-400 text-gray-400 transition-colors inline-block"
                            >
                              <RefreshCw className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleDeletePolicy(doc.document_id)}
                              title="Delete Document"
                              className="p-1 hover:text-rose-400 text-gray-400 transition-colors inline-block"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: UPLOAD DOCUMENT */}
      {activeTab === 'upload' && (
        <div className="max-w-2xl mx-auto bg-gray-900 border border-gray-800 rounded-2xl p-8 space-y-6">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Upload className="w-5 h-5 text-cyan-400" /> Upload Hospital Policy Document
            </h2>
            <p className="text-xs text-gray-400 mt-1">
              Uploaded files are validated, chunked (~800 characters), embedded with ONNX MiniLM, and persisted into ChromaDB.
            </p>
          </div>

          {uploadSuccess && (
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-xs text-emerald-400 flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>{uploadSuccess}</span>
            </div>
          )}

          <form onSubmit={handleUploadSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
                Document File (.pdf, .docx, .txt)
              </label>
              <div className="border-2 border-dashed border-gray-700 hover:border-cyan-500/60 rounded-xl p-6 text-center transition-colors cursor-pointer bg-gray-950/40">
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={(e) => setUploadFile(e.target.files[0])}
                  className="hidden"
                  id="policy-file-input"
                />
                <label htmlFor="policy-file-input" className="cursor-pointer space-y-2 block">
                  <FileText className="w-8 h-8 text-cyan-400 mx-auto" />
                  <span className="text-xs text-gray-300 block">
                    {uploadFile ? uploadFile.name : 'Click to select or drag and drop document'}
                  </span>
                  <span className="text-[11px] text-gray-400 block font-mono">
                    Supported: PDF, DOCX, TXT (Max 20MB)
                  </span>
                </label>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                Document Title (Optional)
              </label>
              <input
                type="text"
                value={uploadTitle}
                onChange={(e) => setUploadTitle(e.target.value)}
                placeholder="e.g., Inpatient Bed Allocation Guidelines 2024"
                className="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                Hospital Department
              </label>
              <select
                value={uploadDept}
                onChange={(e) => setUploadDept(e.target.value)}
                className="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-cyan-500"
              >
                <option value="General">General Hospital Policy</option>
                <option value="Hospital Administration">Hospital Administration</option>
                <option value="Outpatient Services">Outpatient Services</option>
                <option value="Bed Management">Bed Management</option>
                <option value="Emergency Medicine">Emergency Medicine</option>
                <option value="Patient Admissions">Patient Admissions</option>
                <option value="Clinical Quality">Clinical Quality</option>
                <option value="Nursing Administration">Nursing Administration</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={isUploading || !uploadFile}
              className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-500 text-black font-semibold text-xs rounded-xl shadow-lg shadow-cyan-500/20 hover:opacity-95 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isUploading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Ingesting & Embedding into ChromaDB...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" /> Upload & Index Policy Document
                </>
              )}
            </button>
          </form>
        </div>
      )}

      {/* CHUNKS MODAL */}
      {selectedDocChunks && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl max-w-3xl w-full max-h-[80vh] flex flex-col overflow-hidden">
            <div className="p-5 border-b border-gray-800 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Layers className="w-4 h-4 text-cyan-400" />
                  {selectedDocChunks.doc.title}
                </h3>
                <span className="text-xs text-gray-400 font-mono">
                  {selectedDocChunks.chunks.length} Chunks in ChromaDB • {selectedDocChunks.doc.department}
                </span>
              </div>
              <button
                onClick={() => setSelectedDocChunks(null)}
                className="px-3 py-1 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-xs font-semibold"
              >
                Close
              </button>
            </div>

            <div className="p-5 overflow-y-auto space-y-4">
              {selectedDocChunks.chunks.map((chk, idx) => (
                <div key={idx} className="p-4 bg-gray-950 border border-gray-800 rounded-xl space-y-2">
                  <div className="flex items-center justify-between text-xs text-gray-400 font-mono border-b border-gray-800/60 pb-1.5">
                    <span className="text-cyan-400 font-semibold">Chunk #{chk.chunk_index + 1}</span>
                    <span>Page {chk.page_number || 1} • {chk.token_count} words</span>
                  </div>
                  {chk.section_header && (
                    <div className="text-xs font-semibold text-gray-200">
                      Header: {chk.section_header}
                    </div>
                  )}
                  <p className="text-xs text-gray-300 font-sans whitespace-pre-wrap leading-relaxed">
                    {chk.content}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
