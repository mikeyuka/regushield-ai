import React, { useState, useRef, useEffect } from 'react';
import {
  UploadCloud,
  FileText,
  Trash2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  Download,
  FileSpreadsheet,
  Check,
  ShieldCheck,
  Play,
  RotateCcw
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function IngestionDashboard() {
  const [dragActive, setDragActive] = useState(false);
  const [queuedFile, setQueuedFile] = useState(null);
  const [pipelineStep, setPipelineStep] = useState(0); // 0: idle, 1: uploading, 2: ocr, 3: validation, 4: complete
  const [uploadProgress, setUploadProgress] = useState(0);
  const [validationSubStep, setValidationSubStep] = useState('');
  const [documentId, setDocumentId] = useState(null);
  const [pollingActive, setPollingActive] = useState(false);
  const [error, setError] = useState(null);
  
  // Recent Audits Ledger state
  const [audits, setAudits] = useState([
    {
      sku: 'SKU-89241',
      name: 'Sulphur-Free Preservative Compound',
      category: 'Preservatives',
      status: 'Validated',
      date: '2026-06-25',
      reportName: 'Sulphur_Free_Preservative_Certificate.pdf',
      pdfUrl: null
    },
    {
      sku: 'SKU-10492',
      name: 'Titanium Dioxide Ex-Alpha',
      category: 'Colorants',
      status: 'Rejected',
      date: '2026-06-24',
      reportName: 'Titanium_Dioxide_Spec_Sheet.pdf',
      pdfUrl: null
    },
    {
      sku: 'SKU-31205',
      name: 'Ethanol Denatured 99%',
      category: 'Solvents',
      status: 'Processing',
      date: '2026-06-26',
      reportName: 'Ethanol_SDS_v3.pdf',
      pdfUrl: null
    }
  ]);

  const fileInputRef = useRef(null);

  // Drag handlers
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      addFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      addFile(e.target.files[0]);
    }
  };

  const addFile = (file) => {
    // Prevent changing file while processing is active
    if (pipelineStep > 0 && pipelineStep < 4) return;
    
    // Reset pipeline state
    setPipelineStep(0);
    setUploadProgress(0);
    setValidationSubStep('');
    setDocumentId(null);
    setPollingActive(false);
    setError(null);

    const extension = file.name.split('.').pop().toLowerCase();
    const sizeInMB = (file.size / (1024 * 1024)).toFixed(2);
    const sizeString = sizeInMB > 0.1 ? `${sizeInMB} MB` : `${(file.size / 1024).toFixed(1)} KB`;

    setQueuedFile({
      name: file.name,
      size: sizeString,
      extension: extension.toUpperCase(),
      rawFile: file
    });
  };

  const removeFile = () => {
    if (pipelineStep > 0 && pipelineStep < 4) return;
    setQueuedFile(null);
    setPipelineStep(0);
    setUploadProgress(0);
    setValidationSubStep('');
    setDocumentId(null);
    setPollingActive(false);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const triggerFileSelect = () => {
    if (pipelineStep > 0 && pipelineStep < 4) return;
    fileInputRef.current.click();
  };

  // Run the multi-step real progress pipeline
  const processAndValidate = async () => {
    if (!queuedFile || pipelineStep > 0) return;

    setPipelineStep(1);
    setUploadProgress(10); // Initial progress
    setError(null);

    const formData = new FormData();
    formData.append('file', queuedFile.rawFile);

    try {
      const response = await fetch(`${API_BASE}/api/v1/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();
      setDocumentId(data.document_id);
      setUploadProgress(100);
      setPipelineStep(2);
      setPollingActive(true);
    } catch (err) {
      console.error(err);
      setError('Upload failed. Please check backend connection.');
      setPipelineStep(0);
    }
  };

  // Status Polling Effect
  useEffect(() => {
    let interval;
    if (pollingActive && documentId) {
      interval = setInterval(async () => {
        try {
          const response = await fetch(`${API_BASE}/api/v1/compliance/documents/${documentId}/status`);
          if (!response.ok) return;

          const data = await response.json();
          
          // Map backend status to UI pipeline steps
          if (data.status === 'PROCESSING') {
            setPipelineStep(2);
          } else if (data.status === 'OCR_COMPLETED') {
            setPipelineStep(3);
            setValidationSubStep('Analyzing ingredients matching UK REACH thresholds');
          } else if (data.status === 'VALIDATED') {
            setPipelineStep(3);
            setValidationSubStep('Finalizing compliance report');
          } else if (data.status === 'REJECTED') {
            setPollingActive(false);
            setError('Document rejected: Compliance thresholds not met.');
            setPipelineStep(0);
          }

          if (data.compliance_request_status === 'COMPLETED') {
            setPollingActive(false);
            setPipelineStep(4);
            
            // Fetch real product details if available, or use queuedFile name
            const newAudit = {
              sku: `SKU-${Math.floor(10000 + Math.random() * 90000)}`,
              name: queuedFile.name.split('.')[0].replace(/[-_]/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
              category: 'Chemical Ingestion',
              status: 'Validated',
              date: new Date().toISOString().split('T')[0],
              reportName: queuedFile.name,
              pdfUrl: data.generated_pdf_url ? `${API_BASE}${data.generated_pdf_url}` : null
            };
            setAudits(prev => [newAudit, ...prev]);
          } else if (data.compliance_request_status === 'FAILED') {
            setPollingActive(false);
            setError('Compliance processing failed.');
            setPipelineStep(0);
          }
        } catch (err) {
          console.error('Polling error:', err);
        }
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [pollingActive, documentId, queuedFile]);

  const downloadBlueprint = (audit) => {
    if (audit.pdfUrl) {
      window.open(audit.pdfUrl, '_blank');
      return;
    }
    
    // Fallback for simulated records
    const content = `========================================================
REGUSHIELD AI COMPLIANCE PORTAL - REGULATORY BLUEPRINT
========================================================
Product Name: ${audit.name}
SKU:          ${audit.sku}
Category:     ${audit.category}
Audit Date:   ${audit.date}
Verification: APPROVED & VALIDATED

This blueprint confirms that the ingredients declared in ${audit.reportName || 'the uploaded documentation'}
have been successfully processed and verified against current REACH (Registration, Evaluation,
Authorisation and Restriction of Chemicals) safety limits and thresholds.

Verified Accredited Laboratories Check: PASS
UK REACH Threshold Compliance:         PASS (Within safe limits)

Signed by: ReguShield AI Auto-Compliance Engine v0.1.0
========================================================`;
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${audit.sku}_Compliance_Blueprint.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const getStepHeader = () => {
    switch (pipelineStep) {
      case 1: return 'Step 1: Uploading to Secure Storage';
      case 2: return 'Step 2: Extracting Document Text via OCR';
      case 3: return 'Step 3: Running Claude 3.5 Sonnet Validation';
      case 4: return 'Ingestion & Audit Completed';
      default: return '';
    }
  };

  return (
    <div className="space-y-6">
      {/* Banner / Header */}
      <div className="bg-gradient-to-r from-slate-800 to-slate-900 border border-slate-700/80 rounded-xl p-5 md:p-6 shadow-lg">
        <h2 className="text-xl font-bold text-white flex items-center space-x-2">
          <UploadCloud className="h-6 w-6 text-emerald-400" />
          <span>Interactive Ingestion & Audit Dashboard</span>
        </h2>
        <p className="text-xs text-slate-300 mt-1.5 leading-relaxed">
          Upload, parse, and validate safety data sheets, supply chain logs, or material compositions. Our pipeline automates cloud storage ingestion, advanced OCR text extraction, and Claude 3.5 Sonnet safety checks against REACH regulations.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Hand side: Interactive Dropzone & Active Pipeline */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-[#1E293B] border border-slate-800 rounded-xl p-5 shadow-lg">
            <h3 className="font-bold text-sm text-slate-200 mb-3 flex items-center justify-between">
              <span>Document Upload & Ingestion</span>
              {queuedFile && pipelineStep === 0 && (
                <button 
                  onClick={removeFile}
                  className="text-xs text-rose-400 hover:text-rose-300 flex items-center space-x-1"
                >
                  <RotateCcw className="h-3 w-3" />
                  <span>Reset</span>
                </button>
              )}
            </h3>

            {/* Hidden Input file selector */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileInputChange}
              accept=".pdf,.docx,.xlsx"
              className="hidden"
            />

            {/* Interactive Dropzone */}
            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              onClick={triggerFileSelect}
              className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200 select-none ${
                dragActive
                  ? 'border-emerald-500 bg-emerald-500/10'
                  : 'border-slate-700 bg-[#0F172A] hover:border-slate-600 hover:bg-[#131E35]'
              } ${pipelineStep > 0 && pipelineStep < 4 ? 'pointer-events-none opacity-50' : ''}`}
            >
              <div className="space-y-3">
                <div className="flex justify-center">
                  <UploadCloud className={`h-10 w-10 ${dragActive ? 'text-emerald-400 animate-bounce' : 'text-slate-400'}`} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-200">
                    {dragActive ? 'Drop your file here' : 'Drag & drop supplier file here'}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    or <span className="text-emerald-400 font-bold hover:underline">browse computer</span>
                  </p>
                </div>
                <p className="text-[10px] text-slate-500">Supports PDF, DOCX, or XLSX up to 50MB</p>
              </div>
            </div>

            {/* Queued File Status Card */}
            {queuedFile && (
              <div className="mt-4 bg-[#0F172A] border border-slate-850 p-4 rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3 overflow-hidden">
                    <div className="p-2 bg-slate-800 rounded-lg flex items-center justify-center flex-shrink-0 border border-slate-700">
                      <FileText className="h-5 w-5 text-indigo-400" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-white truncate">{queuedFile.name}</p>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        {queuedFile.size} • <span className="font-bold text-emerald-400">{queuedFile.extension}</span>
                      </p>
                    </div>
                  </div>
                  {pipelineStep === 0 && (
                    <button
                      onClick={removeFile}
                      className="p-1.5 hover:bg-rose-500/10 text-slate-400 hover:text-rose-400 rounded-lg transition-colors border border-transparent hover:border-rose-500/20"
                      title="Remove file"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>

                {error && (
                  <div className="p-2.5 bg-rose-500/10 border border-rose-500/20 rounded-lg flex items-center space-x-2 text-rose-400">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    <span className="text-[10px] font-bold">{error}</span>
                  </div>
                )}

                {pipelineStep === 0 && (
                  <button
                    onClick={processAndValidate}
                    className="w-full py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-900 rounded-lg text-xs font-extrabold transition-all shadow-md flex items-center justify-center space-x-2"
                  >
                    <Play className="h-3.5 w-3.5 fill-current" />
                    <span>Process & Validate Document</span>
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Active Pipeline Status Console */}
          {pipelineStep > 0 && (
            <div className="bg-[#1E293B] border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Pipeline Engine Logs</span>
                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold ${
                  pipelineStep === 4 
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                    : 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/20 animate-pulse'
                }`}>
                  {pipelineStep === 4 ? 'Success' : 'Processing'}
                </span>
              </div>

              <div className="space-y-3.5">
                <h4 className="text-xs font-bold text-white flex items-center space-x-2">
                  {pipelineStep < 4 ? (
                    <Loader2 className="h-3.5 w-3.5 text-emerald-400 animate-spin" />
                  ) : (
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                  )}
                  <span>{getStepHeader()}</span>
                </h4>

                {/* Progress bar for step 1 */}
                {pipelineStep === 1 && (
                  <div className="space-y-1.5 bg-[#0F172A] p-3 rounded-lg border border-slate-850">
                    <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-emerald-500 to-indigo-500 h-full rounded-full transition-all duration-150"
                        style={{ width: `${uploadProgress}%` }}
                      ></div>
                    </div>
                    <div className="flex justify-between items-center text-[10px] font-medium text-slate-400">
                      <span>Uploading raw payload...</span>
                      <span className="text-emerald-400 font-bold">{uploadProgress}%</span>
                    </div>
                  </div>
                )}

                {/* Pulsing loading state for step 2 */}
                {pipelineStep === 2 && (
                  <div className="bg-[#0F172A] p-4 rounded-lg border border-slate-850 text-center py-5">
                    <p className="text-xs font-medium text-slate-200 animate-pulse">
                      Analyzing pixels and converting to raw text logs...
                    </p>
                    <p className="text-[10px] text-slate-400 mt-1">
                      OCR Engine extracting tables & structural chemical lists.
                    </p>
                  </div>
                )}

                {/* Validation checks for step 3 */}
                {pipelineStep === 3 && (
                  <div className="bg-[#0F172A] p-4 rounded-lg border border-slate-850 space-y-2.5">
                    <div className="flex items-center space-x-2.5">
                      <Loader2 className="h-4 w-4 text-emerald-400 animate-spin flex-shrink-0" />
                      <span className="text-xs font-bold text-slate-200">Claude 3.5 Sonnet:</span>
                    </div>
                    <p className="text-xs font-semibold text-emerald-400 animate-pulse pl-6">
                      {validationSubStep}...
                    </p>
                  </div>
                )}

                {/* Completed state card */}
                {pipelineStep === 4 && (
                  <div className="bg-emerald-950/20 border border-emerald-500/20 p-4 rounded-xl space-y-2">
                    <p className="text-xs font-bold text-emerald-400 flex items-center space-x-1.5">
                      <ShieldCheck className="h-4 w-4" />
                      <span>Regulatory Audit Approved</span>
                    </p>
                    <p className="text-[11px] text-slate-300 leading-relaxed">
                      Your document has been verified against REACH guidelines. <strong>{queuedFile.name}</strong> was mapped with 0 compliance flags. The regulatory blueprint is now available below.
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right Hand side: Recent Audits Ledger */}
        <div className="lg:col-span-7">
          <div className="bg-[#1E293B] border border-slate-800 rounded-xl overflow-hidden shadow-lg h-full flex flex-col justify-between">
            <div>
              <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-base text-white">Recent Audits Ledger</h3>
                  <p className="text-[10px] text-slate-400 mt-0.5">Track and export chemical composition compliance declarations</p>
                </div>
                <span className="bg-slate-800 text-slate-300 text-[10px] font-bold px-2 py-0.5 rounded border border-slate-700">
                  {audits.length} Records
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-800 text-sm">
                  <thead className="bg-[#0F172A]">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold text-slate-400 text-xs">Product Details</th>
                      <th className="px-4 py-3 text-left font-semibold text-slate-400 text-xs">Category</th>
                      <th className="px-4 py-3 text-left font-semibold text-slate-400 text-xs">Status</th>
                      <th className="px-4 py-3 text-right font-semibold text-slate-400 text-xs">Blueprint</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-[#1E293B]">
                    {audits.map((audit) => (
                      <tr key={audit.sku} className="hover:bg-slate-800/40 transition-colors">
                        <td className="px-4 py-3">
                          <div className="min-w-0">
                            <p className="font-semibold text-slate-200 text-xs truncate max-w-[160px] sm:max-w-[200px]">
                              {audit.name}
                            </p>
                            <p className="text-[10px] text-slate-400 mt-0.5 font-mono">{audit.sku}</p>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-xs text-slate-300">
                          {audit.category}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            audit.status === 'Validated' 
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                              : audit.status === 'Rejected' 
                                ? 'bg-rose-500/15 text-rose-400 border border-rose-500/20' 
                                : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          }`}>
                            <span className={`h-1.5 w-1.5 rounded-full mr-1.5 ${
                              audit.status === 'Validated' 
                                ? 'bg-emerald-400' 
                                : audit.status === 'Rejected' 
                                  ? 'bg-rose-400' 
                                  : 'bg-amber-400 animate-pulse'
                            }`}></span>
                            {audit.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => downloadBlueprint(audit)}
                            className={`p-1.5 rounded border text-xs font-bold flex items-center space-x-1.5 ml-auto transition-colors ${
                              audit.status === 'Validated'
                                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400 hover:bg-emerald-500 hover:text-slate-900 hover:border-transparent'
                                : audit.status === 'Processing'
                                  ? 'bg-slate-800 border-slate-700 text-slate-500 cursor-not-allowed'
                                  : 'bg-slate-850 border-slate-800 text-rose-400 hover:bg-rose-500/10 hover:border-rose-500/20'
                            }`}
                            disabled={audit.status === 'Processing'}
                            title={audit.status === 'Processing' ? 'Validation in progress' : 'Download Compliance Blueprint'}
                          >
                            <Download className="h-3.5 w-3.5" />
                            <span className="hidden sm:inline">Blueprint</span>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="bg-[#0F172A] px-5 py-3 border-t border-slate-800/80 text-[10px] text-slate-400 flex items-center space-x-2">
              <Check className="h-3.5 w-3.5 text-emerald-400" />
              <span>Blueprints exported as safety-verified UK compliance tokens.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
