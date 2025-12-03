import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import ScenarioSelection from './pages/ScenarioSelection';
import CallHistory from './pages/CallHistory';
import CallReview from './pages/CallReview';
import Layout from './components/Layout';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/scenarios" replace />} />
          <Route path="scenarios" element={<ScenarioSelection />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="history" element={<CallHistory />} />
          <Route path="review/:callId" element={<CallReview />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
