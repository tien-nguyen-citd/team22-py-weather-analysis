import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NangMuaApp } from './NangMuaApp';
import { AdminPage } from './pages/AdminPage';
import { LoginPage } from './pages/LoginPage';

// Create a query client with 30-minute stale time
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 60 * 1000, // 30 minutes
      refetchOnWindowFocus: false,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/admin/dang-nhap" element={<LoginPage />} />
          <Route path="/admin/*" element={<Navigate to="/admin" replace />} />

          {/* Main Weather Analysis App Routes */}
          <Route path="/" element={<NangMuaApp />} />
          <Route path="/:page" element={<NangMuaApp />} />

          {/* Catch-all fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
