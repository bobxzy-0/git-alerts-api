import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/context/AuthContext';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Layout } from '@/components/Layout';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { Home } from '@/pages/Home';
import { Login } from '@/pages/Login';
import { Dashboard } from '@/pages/Dashboard';
import { ScanWorkspace } from '@/pages/ScanWorkspace';
import { NewScan } from '@/pages/NewScan';
import { ScanDetail } from '@/pages/ScanDetail';
import { Findings } from '@/pages/Findings';
import { Integrations } from '@/pages/Integrations';
import { Settings } from '@/pages/Settings';
import { SourceHealth } from '@/pages/SourceHealth';
import { Notifications } from '@/pages/Notifications';
import { LanguageProvider } from '@/i18n/LanguageContext';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <LanguageProvider>
        <AuthProvider>
          <Router>
            <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />

            {/* Protected routes with layout */}
            <Route
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<Home />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/scans" element={<ScanWorkspace />} />
              <Route path="/scans/new" element={<NewScan />} />
              <Route path="/scans/:id" element={<ScanDetail />} />
              <Route path="/findings" element={<Findings />} />
              <Route path="/integrations" element={<Integrations />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/monitoring" element={<Navigate to="/scans?tab=monitors" replace />} />
              <Route path="/monitor-rules" element={<Navigate to="/scans?tab=monitors" replace />} />
              <Route path="/source-health" element={<SourceHealth />} />
              <Route path="/notifications" element={<Notifications />} />
              <Route path="/monitoring-profiles" element={<Navigate to="/scans?tab=monitors" replace />} />
              <Route path="/excluded-repositories" element={<Navigate to="/settings?tab=exclusions" replace />} />
            </Route>

            {/* Catch all */}
            <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Router>
        </AuthProvider>
      </LanguageProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
