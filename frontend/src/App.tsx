import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { GuestRoute, ProtectedRoute } from './auth/ProtectedRoute';
import { MainLayout } from './pages/MainLayout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { SalesPage } from './pages/SalesPage';
import { ForecastPage } from './pages/ForecastPage';
import { SuppliesPage } from './pages/SuppliesPage';
import { PickingPage } from './pages/PickingPage';
import { PickingDetailPage } from './pages/PickingDetailPage';
import { ReportsPage } from './pages/ReportsPage';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<GuestRoute />}>
            <Route path="/login" element={<LoginPage />} />
          </Route>
          <Route element={<ProtectedRoute />}>
            <Route element={<MainLayout />}>
              <Route index element={<DashboardPage />} />
              <Route path="/sales" element={<SalesPage />} />
              <Route path="/forecast" element={<ForecastPage />} />
              <Route path="/supplies" element={<SuppliesPage />} />
              <Route path="/picking" element={<PickingPage />} />
              <Route path="/picking/:shopId" element={<PickingDetailPage />} />
              <Route path="/reports" element={<ReportsPage />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
