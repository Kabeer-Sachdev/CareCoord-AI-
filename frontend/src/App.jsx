import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginPage } from './pages/Login';
import { Sidebar } from './components/Sidebar';
import { Topbar } from './components/Topbar';
import { OverviewPage } from './pages/Overview';
import { PatientsPage } from './pages/Patients';
import { DoctorsPage } from './pages/Doctors';
import { AppointmentsPage } from './pages/Appointments';
import { AiAgentsPage } from './pages/AiAgents';
import { WorkflowRequestPage } from './pages/WorkflowRequest';
import { WorkflowHistoryPage } from './pages/WorkflowHistory';
import { PoliciesPage } from './pages/Policies';
import { PredictionsPage } from './pages/Predictions';
import { OptimizationPage } from './pages/Optimization';
import { IntegrationsPage } from './pages/Integrations';

// Phase 4 Role Portals
import { DoctorPortal } from './pages/DoctorPortal';
import { ReceptionPortal } from './pages/ReceptionPortal';
import { NursePortal } from './pages/NursePortal';
import { PatientPortal } from './pages/PatientPortal';

function getDefaultPageForRole(role) {
  switch (role) {
    case 'DOCTOR':
      return 'doctor-portal';
    case 'RECEPTIONIST':
      return 'reception-portal';
    case 'NURSE':
      return 'nurse-portal';
    case 'PATIENT':
      return 'patient-portal';
    case 'ADMIN':
    default:
      return 'overview';
  }
}

function MainLayout() {
  const { isAuthenticated, role, user } = useAuth();
  const [currentPage, setCurrentPage] = useState('overview');
  const [lastWorkflowEvent, setLastWorkflowEvent] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Sync default page when user role loads
  useEffect(() => {
    if (role) {
      setCurrentPage(getDefaultPageForRole(role));
    }
  }, [role]);

  if (!isAuthenticated) {
    return (
      <LoginPage 
        onLogin={() => {
          const u = JSON.parse(localStorage.getItem('cc_user') || '{}');
          setCurrentPage(getDefaultPageForRole(u.role));
        }} 
      />
    );
  }

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
    }, 600);
  };

  const handleExecuteWorkflow = (eventData) => {
    setLastWorkflowEvent(eventData);
  };

  const handleLogout = () => {
    setCurrentPage('overview');
  };

  return (
    <div className="flex min-h-screen bg-dark-900 text-gray-100 font-sans">
      {/* Sidebar Navigation */}
      <Sidebar 
        currentPage={currentPage} 
        setCurrentPage={setCurrentPage}
        onLogout={handleLogout}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <Topbar
          title={currentPage.replace('-', ' ')}
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
          onLogout={handleLogout}
        />

        {/* Page Content View */}
        <main className="p-6 flex-1 max-w-7xl w-full mx-auto">
          {/* Phase 4 Role Portals */}
          {currentPage === 'doctor-portal' && <DoctorPortal />}
          {currentPage === 'reception-portal' && <ReceptionPortal />}
          {currentPage === 'nurse-portal' && <NursePortal />}
          {currentPage === 'patient-portal' && <PatientPortal />}

          {/* Phase 5 RAG Policy Intelligence */}
          {currentPage === 'policies' && <PoliciesPage />}

          {/* Phase 6 ML Predictive Analytics */}
          {currentPage === 'predictions' && <PredictionsPage />}

          {/* Phase 7 Resource Optimization Engine */}
          {currentPage === 'optimization' && <OptimizationPage />}

          {/* Phase 8 External MCP & FHIR Integrations */}
          {currentPage === 'integrations' && <IntegrationsPage />}

          {/* Phase 1-3 Pages */}
          {currentPage === 'overview' && (
            <OverviewPage
              onNavigateToWorkflow={() => setCurrentPage('workflow')}
              lastWorkflowEvent={lastWorkflowEvent}
            />
          )}

          {currentPage === 'patients' && <PatientsPage />}
          {currentPage === 'doctors' && <DoctorsPage />}
          {currentPage === 'appointments' && <AppointmentsPage />}
          {currentPage === 'ai-agents' && <AiAgentsPage />}

          {currentPage === 'workflow' && (
            <WorkflowRequestPage onExecuteWorkflow={handleExecuteWorkflow} />
          )}

          {currentPage === 'workflows' && <WorkflowHistoryPage />}
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainLayout />
    </AuthProvider>
  );
}