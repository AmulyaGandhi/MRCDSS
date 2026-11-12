import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Overview from './pages/Overview';
import DistrictExplorer from './pages/DistrictExplorer';
import DistrictDetails from './pages/DistrictDetails';
import RiskAnalysis from './pages/RiskAnalysis';
import PlanningPriorities from './pages/Planning';
import Methodology from './pages/Methodology';
import RecentHmis from './pages/RecentHmis';
import About from './pages/About';
import Assistant from './components/Assistant';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/districts" element={<DistrictExplorer />} />
        <Route path="/districts/:state/:district" element={<DistrictDetails />} />
        <Route path="/risk-analysis" element={<RiskAnalysis />} />
        <Route path="/planning" element={<PlanningPriorities />} />
        <Route path="/methodology" element={<Methodology />} />
        <Route path="/recent-hmis" element={<RecentHmis />} />
        <Route path="/about" element={<About />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Assistant />
    </BrowserRouter>
  );
}

export default App;
