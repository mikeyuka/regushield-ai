import React, { useState } from 'react';
import {
  LayoutDashboard,
  UploadCloud,
  CreditCard,
  FileText,
  Clock,
  ArrowRight,
  Menu,
  X,
  ShieldCheck,
  LogOut
} from 'lucide-react';
import IngestionDashboard from './components/IngestionDashboard';
import BillingCheckout from './components/BillingCheckout';
import Login from './components/Login';

export default function App() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('uploads');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  if (!user) {
    return <Login onLogin={setUser} />;
  }

  return (
    <div className="flex flex-col min-h-screen bg-[#0F172A] text-slate-100 font-sans">
      
      {/* Navbar */}
      <header className="sticky top-0 z-40 bg-[#1A365D] border-b border-slate-700 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            
            <div className="flex items-center space-x-3">
              <div className="bg-emerald-500 text-white p-2 rounded-lg flex items-center justify-center">
                <ShieldCheck className="h-6 w-6 text-white" />
              </div>
              <span className="font-bold text-lg md:text-xl tracking-wide bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
                ReguShield AI <span className="text-emerald-400 font-normal text-sm sm:inline hidden">| Compliance Portal</span>
              </span>
            </div>

            <nav className="hidden md:flex space-x-1">
              {[
                { id: 'uploads', label: 'Ingestion' },
                { id: 'billing', label: 'Billing' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
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

        {mobileMenuOpen && (
          <div className="md:hidden bg-[#1E3A8A] px-2 pt-2 pb-3 space-y-1 sm:px-3 border-t border-slate-700">
            {[
              { id: 'uploads', label: 'Ingestion' },
              { id: 'billing', label: 'Billing' }
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

      <div className="flex-1 flex flex-col md:flex-row max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 gap-6">
        
        <aside className="w-full md:w-64 flex-shrink-0">
          <div className="bg-[#1E293B] border border-slate-800 rounded-xl p-4 sticky top-24 shadow-lg space-y-6">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Navigation</p>
              <div className="space-y-1">
                {[
                  { id: 'uploads', label: 'Upload Ingestion', icon: UploadCloud },
                  { id: 'billing', label: 'Billing & Checkout', icon: CreditCard }
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
              <div className="flex items-center justify-between bg-[#0F172A] p-2.5 rounded-lg border border-slate-800">
                <div className="flex items-center space-x-3 overflow-hidden">
                  <div className="h-8 w-8 rounded-full bg-emerald-500/20 text-emerald-400 flex-shrink-0 flex items-center justify-center font-bold text-sm">
                    {user.name.substring(0, 2).toUpperCase()}
                  </div>
                  <div className="overflow-hidden">
                    <p className="text-xs font-medium text-white truncate">{user.name}</p>
                    <p className="text-[10px] text-emerald-400 truncate">{user.tier}</p>
                  </div>
                </div>
                <button 
                  onClick={() => setUser(null)}
                  className="p-1 text-slate-500 hover:text-rose-400 transition-colors"
                  title="Logout"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </aside>

        <main className="flex-1 min-w-0">
          {activeTab === 'uploads' && (
            <IngestionDashboard />
          )}

          {activeTab === 'billing' && (
            <BillingCheckout userEmail={user.email} />
          )}
        </main>
      </div>

      <footer className="bg-[#0F172A] border-t border-slate-800 py-6 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="flex items-center space-x-2">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse inline-block"></span>
            <span>ReguShield AI Engine Active • v0.1.0</span>
          </div>
          <div className="text-center md:text-right">
            &copy; {new Date().getFullYear()} ReguShield AI Ltd. All rights reserved.
          </div>
        </div>
      </footer>

    </div>
  );
}
