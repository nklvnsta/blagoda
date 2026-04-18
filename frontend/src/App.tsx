import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { MainLayout } from './pages/MainLayout';
import { DashboardPage } from './pages/DashboardPage';
import { SalesPage } from './pages/SalesPage';
import { ForecastPage } from './pages/ForecastPage';
import { SuppliesPage } from './pages/SuppliesPage';
import { PickingPage } from './pages/PickingPage';
import { PickingDetailPage } from './pages/PickingDetailPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="/sales" element={<SalesPage />} />
          <Route path="/forecast" element={<ForecastPage />} />
          <Route path="/supplies" element={<SuppliesPage />} />
          <Route path="/picking" element={<PickingPage />} />
          <Route path="/picking/:shopId" element={<PickingDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
