import { Bell, ChevronDown } from 'lucide-react';

const TABS = ['Dashboard', 'Deviations', 'CAPAs', 'Documents', 'Reports'];

export const TopNavBar = ({ activeTab = 'Deviations' }: { activeTab?: string }) => {
  const activeIndex = Math.max(0, TABS.indexOf(activeTab));

  return (
    <div className="top-nav">
      <div className="nav-left">
        <div className="logo-container">
          <svg width="34" height="34" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ flexShrink: 0 }}>
            <path d="M12 2L22 20H2L12 2Z" fill="#2563eb"/>
          </svg>
          <div className="logo-text-wrapper">
            <span className="logo-text">AIVOA</span>
            <span className="tagline">AI for a Safer Tomorrow</span>
          </div>
        </div>
      </div>
      
      <div className="nav-center-pill">
        <div 
          className="active-pill-bg"
          style={{ transform: `translateX(${activeIndex * 100}%)` }}
        />
        {TABS.map((tab) => (
          <a 
            key={tab} 
            href={`#${tab}`} 
            className={`nav-link ${activeTab === tab ? 'active' : ''}`}
          >
            {tab}
          </a>
        ))}
      </div>

      <div className="nav-right">
        <div className="company-dropdown">
          Demo Pharma Ltd <ChevronDown size={16} color="#64748b" />
        </div>
        <div className="notification-bell">
          <Bell size={20} />
          <div className="notification-dot"></div>
        </div>
        <div className="user-profile">
          <div className="avatar">AD</div>
          <ChevronDown size={16} color="#64748b" />
        </div>
      </div>
    </div>
  );
};
