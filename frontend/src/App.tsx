
import { useState, useEffect } from 'react';
import { TopNavBar } from './components/TopNavBar';
import { DeviationForm } from './components/DeviationForm';
import { AssistantPanel } from './components/AssistantPanel';

function App() {
  const [activeTab, setActiveTab] = useState(() => {
    const hash = window.location.hash.replace('#', '');
    return hash || 'Deviations';
  });

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      setActiveTab(hash || 'Deviations');
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  return (
    <div className="app-wrapper">
      <TopNavBar activeTab={activeTab} />
      <div className="main-content-area">
        {activeTab === 'Deviations' ? (
          <div className="panels-container">
            <DeviationForm />
            <AssistantPanel />
          </div>
        ) : (
          <div className="placeholder-page">
            <h2>{activeTab} Module</h2>
            <p>This module is currently under development and will be available in a future release.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
