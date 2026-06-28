import React, { useState } from 'react';
import {
  LayoutDashboard,
  UploadCloud,
  CreditCard,
  Activity,
  FileText,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Info,
  ShieldAlert,
  Clock,
  ArrowRight,
  Menu,
  X,
  ChevronRight,
  ShieldCheck,
  Zap,
  DollarSign
} from 'lucide-react';
import IngestionDashboard from './components/IngestionDashboard';
import BillingCheckout from './components/BillingCheckout';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([
    { id: 1, name: 'GDPR_Compliance_Policy_v2.1.pdf', size: '2.4 MB', date: '2026-06-20', status: 'Approved', type: 'PDF' },
    { id: 2, name: 'Terms_Of_Service_Final_Draft.docx', size: '1.1 MB', date: '2026-06-22', status: 'Approved', type: 'DOCX' },
    { id: 3, name: 'Financial_Ingestion_Q2_Statement.xlsx', size: '4.8 MB', date: '2026-06-25', status: 'Parsing', type: 'XLSX' },
    { id: 4, name: 'Privacy_Notice_Updates.pdf', size: '920 KB', date: '2026-06-26', status: 'Flagged', type: 'PDF' }
  ]);
  const [isUploading, setIsUploaded] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Drag and Drop handlers
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
      simulateFileUpload(e.dataTransfer.files[0].name);
    }
  };

  const simulateFileUpload = (filename) => {
    setIsUploaded(true);
    setUploadProgress(0);
    
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => {
            const newFile = {
              id: Date.now(),
              name: filename,
              size: '1.2 MB',
              date: new Date().toISOString().split('T')[0],
              status: 'Parsing',
              type: filename.split('.').pop().toUpperCase() || 'UNKNOWN'
            };
            setUploadedFiles(prevFiles => [newFile, ...prevFiles]);
            setIsUploaded(false);
          }, 500);
          return 100;
        }
        return prev + 10;
      });
    }, 150);
  };

  const triggerMockUpload = () => {
    simulateFileUpload('Security_Assessment_Form_v4.pdf');
  };

  return (
    <div className="flex flex-col min-h-screen bg-[#0F172A] text-slate-100 font-sans">
      
      {/* Navbar in dark navy #1A365D as required */}
      <header className="sticky top-0 z-40 bg-[#1A365D] border-b border-slate-700 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            
            {/* Brand Logo & Header */}
            <div className="flex items-center space-x-3">
              <div className="bg-emerald-500 text-white p-2 rounded-lg flex items-center justify-center">
                <ShieldCheck className="h-6 w-6 text-white" />
              </div>
              <span className="font-bold text-lg md:text-xl tracking-wide bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
                ReguShield AI <span className="text-emerald-400 font-normal text-sm sm:inline hidden">| Compliance Portal</span>
              </span>
            </div>

            {/* Desktop Navbar Links */}
            <nav className="hidden md:flex space-x-1">
              {[
                { id: 'dashboard', label: 'Dashboard' },
                { id: 'uploads', label: 'Uploads' },
                { id: 'billing', label: 'Billing' },
                { id: 'health', label: 'Health' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id);
                    setMobileMenuOpen(false);
                  }}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors duration-150 ${
                    activeTab === tab.id
                      ? 'bg-slate-800 text-white shadow-inner border border-slate-600'
                      : 'text-slate-300 hover:bg-[#2A4D7C] hover:text-white'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>

            {/* Mobile menu button */}
            <div className="md:hidden flex">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="inline-flex items-center justify-center p-2 rounded-md text-slate-300 hover:text-white hover:bg-[#2A4D7C] focus:outline-none"
              >
                {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
            </div>

          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-[#1E3A8A] px-2 pt-2 pb-3 space-y-1 sm:px-3 border-t border-slate-700">
            {[
              { id: 'dashboard', label: 'Dashboard' },
              { id: 'uploads', label: 'Uploads' },
              { id: 'billing', label: 'Billing' },
              { id: 'health', label: 'Health' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id);
                  setMobileMenuOpen(false);
                }}
                className={`w-full text-left block px-3 py-2 rounded-md text-base font-medium ${
                  activeTab === tab.id
                    ? 'bg-slate-800 text-white border-l-4 border-emerald-500'
                    : 'text-slate-300 hover:bg-[#2A4D7C] hover:text-white'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        )}
      </header>

      {/* Main Layout Body containing Sidebar and Viewport */}
      <div className="flex-1 flex flex-col md:flex-row max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 gap-6">
        
        {/* Left Sidebar (Responsive, Desktop static, Mobile hidden by default) */}
        <aside className="w-full md:w-64 flex-shrink-0">
          <div className="bg-[#1E293B] border border-slate-800 rounded-xl p-4 sticky top-24 shadow-lg space-y-6">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Navigation</p>
              <div className="space-y-1">
                {[
                  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
                  { id: 'uploads', label: 'Upload Ingestion', icon: UploadCloud },
                  { id: 'billing', label: 'Billing & Checkout', icon: CreditCard },
                  { id: 'health', label: 'Compliance Health', icon: Activity }
                ].map((item) => {
                  const IconComponent = item.icon;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActiveTab(item.id)}
                      className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                        activeTab === item.id
                          ? 'bg-emerald-600 text-white shadow-md shadow-emerald-900/30 font-semibold'
                          : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                      }`}
                    >
                      <IconComponent className="h-5 w-5 flex-shrink-0" />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="border-t border-slate-800 pt-4">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Active Account</p>
              <div className="flex items-center space-x-3 bg-[#0F172A] p-2.5 rounded-lg border border-slate-800">
                <div className="h-8 w-8 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-sm">
                  MU
                </div>
                <div className="overflow-hidden">
                  <p className="text-xs font-medium text-white truncate">Michael Ukaria</p>
                  <p className="text-[10px] text-emerald-400 truncate">Enterprise Client</p>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-emerald-950 to-slate-900 p-4 rounded-lg border border-emerald-500/30">
              <div className="flex items-center space-x-1.5 mb-2">
                <Zap className="h-4 w-4 text-emerald-400" />
                <span className="text-xs font-bold text-emerald-400 uppercase">System Status</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                All regulatory ingestion pipelines are functional. Next policy sync: tonight 00:00 UTC.
              </p>
            </div>
          </div>
        </aside>

        {/* Central Dashboard Routing Viewport */}
        <main className="flex-1 min-w-0">
          
          {/* Dashboard Tab View */}
          {activeTab === 'dashboard' && (
            <div className="space-y-6">
              
              {/* Welcome Card as required */}
              <div className="relative overflow-hidden bg-gradient-to-r from-slate-800 via-slate-850 to-slate-900 border border-slate-700 rounded-2xl p-6 md:p-8 shadow-xl">
                <div className="absolute right-0 top-0 h-48 w-48 bg-emerald-500/10 rounded-full blur-3xl"></div>
                <div className="absolute -left-12 -bottom-12 h-36 w-36 bg-[#1A365D]/30 rounded-full blur-3xl"></div>
                
                <div className="relative z-10 max-w-2xl">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-400/10 text-emerald-400 mb-4 border border-emerald-400/20">
                    Phase 3 Active
                  </span>
                  <h1 className="text-2xl md:text-3.5xl font-extrabold tracking-tight text-white mb-3">
                    Streamlined Financial & Document Compliance Ingestion
                  </h1>
                  <p className="text-sm md:text-base text-slate-300 leading-relaxed mb-6">
                    Welcome to the ReguShield AI Portal. Scaffolding is complete! Upload policy reports, evaluate real-time GDPR/CCPA alignment, and manage secure subscriptions using our upcoming Stripe or GoCardless payment routers.
                  </p>
                  <div className="flex flex-wrap gap-3">
                    <button
                      onClick={() => setActiveTab('uploads')}
                      className="inline-flex items-center justify-center px-4 py-2.5 border border-transparent text-sm font-semibold rounded-lg text-slate-900 bg-emerald-400 hover:bg-emerald-300 transition-colors shadow-lg shadow-emerald-500/15"
                    >
                      <span>Go to Ingestion Portal</span>
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </button>
                    <button
                      onClick={() => setActiveTab('billing')}
                      className="inline-flex items-center justify-center px-4 py-2.5 border border-slate-700 text-sm font-semibold rounded-lg text-slate-300 bg-slate-800/80 hover:bg-slate-850 hover:text-white transition-colors border-b-2"
                    >
                      Setup Subscription
                    </button>
                  </div>
                </div>
              </div>

              {/* Status Stat Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                
                <div className="bg-[#1E293B] border border-slate-800 p-5 rounded-xl flex items-center space-x-4 shadow-lg hover:border-slate-700 transition-colors">
                  <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-lg">
                    <UploadCloud className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-400 uppercase">Documents Ingested</p>
                    <p className="text-2xl font-bold text-white mt-1">14 Active</p>
                    <p className="text-[10px] text-emerald-400 mt-0.5">98.2% parse success</p>
                  </div>
                </div>

                <div className="bg-[#1E293B] border border-slate-800 p-5 rounded-xl flex items-center space-x-4 shadow-lg hover:border-slate-700 transition-colors">
                  <div className="p-3 bg-indigo-500/10 text-indigo-400 rounded-lg">
                    <CreditCard className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-400 uppercase">Payment Status</p>
                    <p className="text-2xl font-bold text-white mt-1">Active Tier</p>
                    <p className="text-[10px] text-slate-400 mt-0.5">Next billing: July 25, 2026</p>
                  </div>
                </div>

                <div className="bg-[#1E293B] border border-slate-800 p-5 rounded-xl flex items-center space-x-4 shadow-lg hover:border-slate-700 transition-colors">
                  <div className="p-3 bg-amber-500/10 text-amber-400 rounded-lg">
                    <Activity className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-400 uppercase">Security Health</p>
                    <p className="text-2xl font-bold text-white mt-1">96 / 100</p>
                    <p className="text-[10px] text-emerald-400 mt-0.5">Optimal performance</p>
                  </div>
                </div>

              </div>

              {/* Recent Activity Table Container */}
              <div className="bg-[#1E293B] border border-slate-800 rounded-xl overflow-hidden shadow-lg">
                <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
                  <h3 className="font-bold text-base text-white">Recent Compliance Tasks</h3>
                  <button onClick={() => setActiveTab('uploads')} className="text-xs font-bold text-emerald-400 hover:text-emerald-300 transition-colors">
                    View Ingestion List
                  </button>
                </div>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-800 text-sm">
                    <thead className="bg-[#0F172A]">
                      <tr>
                        <th className="px-5 py-3 text-left font-semibold text-slate-400">Document / Policy</th>
                        <th className="px-5 py-3 text-left font-semibold text-slate-400">Date Ingested</th>
                        <th className="px-5 py-3 text-left font-semibold text-slate-400">Status</th>
                        <th className="px-5 py-3 text-right font-semibold text-slate-400">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-[#1E293B]">
                      {uploadedFiles.slice(0, 3).map((file) => (
                        <tr key={file.id} className="hover:bg-slate-800/45 transition-colors">
                          <td className="px-5 py-3.5">
                            <div className="flex items-center space-x-3">
                              <FileText className="h-5 w-5 text-indigo-400 flex-shrink-0" />
                              <div className="truncate max-w-xs sm:max-w-sm">
                                <p className="font-medium text-white truncate">{file.name}</p>
                                <p className="text-xs text-slate-400">{file.size} • {file.type}</p>
                              </div>
                            </div>
                          </td>
                          <td className="px-5 py-3.5 text-slate-300">
                            {file.date}
                          </td>
                          <td className="px-5 py-3.5">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
                              file.status === 'Approved' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                              file.status === 'Parsing' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' :
                              'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            }`}>
                              <span className={`h-1.5 w-1.5 rounded-full mr-1.5 ${
                                file.status === 'Approved' ? 'bg-emerald-400' :
                                file.status === 'Parsing' ? 'bg-indigo-400 animate-pulse' :
                                'bg-rose-400'
                              }`}></span>
                              {file.status}
                            </span>
                          </td>
                          <td className="px-5 py-3.5 text-right">
                            <button className="text-xs font-bold text-slate-300 hover:text-white px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700">
                              View Results
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          )}

          {/* Upload Ingestion Tab View */}
          {activeTab === 'uploads' && (
            <IngestionDashboard />
          )}

          {/* Billing & Subscription Checkout View */}
          {activeTab === 'billing' && (
            <BillingCheckout />
          )}

          {/* Compliance Health View */}
          {activeTab === 'health' && (
            <div className="space-y-6">
              
              {/* Compliance checklist overview */}
              <div className="bg-[#1E293B] border border-slate-800 rounded-xl p-5 shadow-lg">
                <h2 className="text-lg font-bold text-white flex items-center space-x-2">
                  <Activity className="h-5 w-5 text-emerald-400" />
                  <span>Real-time Compliance Alignment Checklist</span>
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  We check your active document catalog against multiple global standards automatically. Here is the current validation dashboard.
                </p>
              </div>

              {/* Grid of criteria alignment */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* GDPR policy alignment */}
                <div className="bg-[#1E293B] border border-slate-800 p-5 rounded-xl space-y-4 shadow-lg">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-bold text-sm text-slate-200">GDPR Compliance Requirements</h4>
                      <p className="text-[10px] text-slate-400 mt-0.5">EU General Data Protection Regulation</p>
                    </div>
                    <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-500/15 text-emerald-400 rounded-full border border-emerald-500/20">98% Aligned</span>
                  </div>
                  <div className="space-y-2 text-xs text-slate-300">
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      <span>Article 30 Ingestion records complete</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      <span>Data retention intervals explicitly audited</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <AlertTriangle className="h-4 w-4 text-amber-400" />
                      <span className="text-slate-400">Consent checklist review pending on privacy page</span>
                    </div>
                  </div>
                </div>

                {/* CCPA/CPRA policy alignment */}
                <div className="bg-[#1E293B] border border-slate-800 p-5 rounded-xl space-y-4 shadow-lg">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-bold text-sm text-slate-200">CCPA / CPRA Requirements</h4>
                      <p className="text-[10px] text-slate-400 mt-0.5">California Consumer Privacy Act</p>
                    </div>
                    <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-500/15 text-emerald-400 rounded-full border border-emerald-500/20">100% Aligned</span>
                  </div>
                  <div className="space-y-2 text-xs text-slate-300">
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      <span>Do Not Sell or Share My Info pathways mapped</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      <span>Notice at Collection verification matched</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      <span>Privacy policy link disclosure verified</span>
                    </div>
                  </div>
                </div>

                {/* SOC2 alignment */}
                <div className="bg-[#1E293B] border border-slate-800 p-5 rounded-xl space-y-4 shadow-lg">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-bold text-sm text-slate-200">SOC 2 Type II Controls</h4>
                      <p className="text-[10px] text-slate-400 mt-0.5">Trust Services Criteria (TSC)</p>
                    </div>
                    <span className="px-2 py-0.5 text-[10px] font-bold bg-indigo-500/15 text-indigo-400 rounded-full border border-indigo-500/20">Audit In-Progress</span>
                  </div>
                  <div className="space-y-2 text-xs text-slate-300">
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      <span>Continuous log injection enabled</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Clock className="h-4 w-4 text-indigo-400" />
                      <span>Vulnerability scan logs queue parsing</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      <span>Multi-factor authentication logs tracked</span>
                    </div>
                  </div>
                </div>

                {/* API Integration align */}
                <div className="bg-[#1E293B] border border-slate-800 p-5 rounded-xl space-y-4 shadow-lg">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-bold text-sm text-slate-200">System API & DB Health</h4>
                      <p className="text-[10px] text-slate-400 mt-0.5">Compliance Gateway Core Services</p>
                    </div>
                    <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-500/15 text-emerald-400 rounded-full border border-emerald-500/20">Optimal</span>
                  </div>
                  <div className="space-y-2 text-xs text-slate-300">
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      <span>Ingestion DB connection status: Active</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      <span>Webhook subscription listener: Standby</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      <span>Token authority system: Verified</span>
                    </div>
                  </div>
                </div>

              </div>

            </div>
          )}

        </main>
      </div>

      {/* Modern, clean footer */}
      <footer className="bg-[#0F172A] border-t border-slate-800 py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center space-x-2">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse inline-block"></span>
            <span>ReguShield AI Ingestion Engine Active • Version 0.1.0 (Phase 3 Sandbox)</span>
          </div>
          <div className="text-center md:text-right">
            &copy; {new Date().getFullYear()} ReguShield AI Ltd. All rights reserved. Secure Stripe/GoCardless Gateway Sandbox.
          </div>
        </div>
      </footer>

    </div>
  );
}
