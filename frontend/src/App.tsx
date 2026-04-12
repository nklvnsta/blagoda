import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { MainLayout } from './pages/MainLayout';
import { DashboardPage } from './pages/DashboardPage';
import { SalesPage } from './pages/SalesPage';
import { ForecastPage } from './pages/ForecastPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="/sales" element={<SalesPage />} />
          <Route path="/forecast" element={<ForecastPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
