import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { ToastContainer } from '../feedback/ToastContainer';

export const AppShell: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans antialiased">
      {/* Top command bar */}
      <Header />

      {/* Main layout body */}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main
          id="main-content"
          tabIndex={-1}
          className="flex-1 overflow-y-auto bg-slate-900/30 p-4 sm:p-6 lg:p-8 flex flex-col focus:outline-none"
        >
          <div className="max-w-7xl mx-auto w-full flex-1 flex flex-col">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Global toast notification stack */}
      <ToastContainer />
    </div>
  );
};
