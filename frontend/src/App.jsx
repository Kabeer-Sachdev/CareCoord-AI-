import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Topbar } from './components/Topbar';
import { OverviewPage } from './pages/Overview';
import { PatientsPage } from './pages/Patients';
import { DoctorsPage } from './pages/Doctors';
import { AppointmentsPage } from './pages/Appointments';
import { AiAgentsPage } from './pages/AiAgents';
import { WorkflowRequestPage } from './pages/WorkflowRequest';
import { WorkflowHistoryPage } from './pages/WorkflowHistory';

export default function App() {
  const [currentPage, setCurrentPage] = useState('overview');
  const [lastWorkflowEvent, setLastWorkflowEvent] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
    }, 600);
  };

  const handleExecuteWorkflow = (eventData) => {
    setLastWorkflowEvent(eventData);
  };

  return (
    <div className="flex min-h-screen bg-dark-900 text-gray-100 font-sans">
      {/* Sidebar Navigation */}
      <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <Topbar
          title={currentPage.replace('-', ' ')}
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
        />

        {/* Page Content View */}
        <main className="p-6 flex-1 max-w-7xl w-full mx-auto">
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
