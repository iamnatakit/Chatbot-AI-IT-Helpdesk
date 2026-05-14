import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './Layout'
import ChatUI from './ChatUI'
import ComplianceAgent from './ComplianceAgent'
import TokenMonitor from './TokenMonitor'
import CostMonitor from './CostMonitor'
import BillingHistory from './BillingHistory'
import Response from './Response'

function App() {
  return (
    <Router>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<ChatUI />} />
          <Route path="/compliance" element={<ComplianceAgent />} />
          <Route path="/token-monitor" element={<TokenMonitor />} />
          <Route path="/cost-monitor" element={<CostMonitor />} />
          <Route path="/billing" element={<BillingHistory />} />
          <Route path="/response" element={<Response />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App