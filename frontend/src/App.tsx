import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import ApplicationsList from './pages/ApplicationsList'
import ApplicationForm from './pages/ApplicationForm'
import ApplicationDetail from './pages/ApplicationDetail'
import UnderwritingResults from './pages/UnderwritingResults'
import LenderPolicies from './pages/LenderPolicies'
import LenderDetail from './pages/LenderDetail'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white border-b border-gray-200">
          <div className="max-w-6xl mx-auto px-4 flex items-center gap-8 h-14">
            <span className="font-bold text-gray-900 text-lg">Kaaj</span>
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `text-sm font-medium ${isActive ? 'text-blue-600' : 'text-gray-500 hover:text-gray-900'}`
              }
            >
              Applications
            </NavLink>
            <NavLink
              to="/lenders"
              className={({ isActive }) =>
                `text-sm font-medium ${isActive ? 'text-blue-600' : 'text-gray-500 hover:text-gray-900'}`
              }
            >
              Lender Policies
            </NavLink>
          </div>
        </nav>

        <main className="max-w-6xl mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<ApplicationsList />} />
            <Route path="/applications/new" element={<ApplicationForm />} />
            <Route path="/applications/:id/edit" element={<ApplicationForm />} />
            <Route path="/applications/:id" element={<ApplicationDetail />} />
            <Route path="/applications/:id/results" element={<UnderwritingResults />} />
            <Route path="/lenders" element={<LenderPolicies />} />
            <Route path="/lenders/:id" element={<LenderDetail />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
