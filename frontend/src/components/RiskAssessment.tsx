
import { useSelector } from 'react-redux';
import type { RootState } from '../store/store';
import { ShieldAlert, Sparkles } from 'lucide-react';

export const RiskAssessment: React.FC = () => {
  const form = useSelector((state: RootState) => state.deviation.form);
  const ui = useSelector((state: RootState) => state.deviation.ui);
  const { fieldsRecentlyChanged } = ui;

  const getHighlightClass = (field: string) => 
    fieldsRecentlyChanged.includes(field) ? 'field-highlight' : '';

  const getSeverityColor = (sev: string) => {
    switch(sev) {
      case 'Critical': return 'risk-badge critical';
      case 'Major': return 'risk-badge major';
      case 'Minor': return 'risk-badge minor';
      default: return 'risk-badge default';
    }
  };

  const getImpactColor = (imp: string) => {
    switch(imp) {
      case 'Critical Impact': return 'risk-badge critical';
      case 'Major Impact': return 'risk-badge major';
      case 'Minor Impact': return 'risk-badge minor';
      case 'No Impact': return 'risk-badge default';
      default: return 'risk-badge default';
    }
  };

  return (
    <div className="risk-assessment-box">
      <h3>
        <ShieldAlert size={18} color="#2563eb" /> 
        AI Risk Assessment
        {form.ai_confidence !== null && (
          <span className="confidence-badge" style={{ marginLeft: 'auto' }}>
            Confidence: {(form.ai_confidence * 100).toFixed(0)}%
          </span>
        )}
      </h3>

      <div className="risk-score-row">
        <div className={`risk-score-card ${getHighlightClass('initial_severity')}`}>
          <div className="risk-label">Severity</div>
          <div className={getSeverityColor(form.initial_severity)}>{form.initial_severity || 'N/A'}</div>
        </div>
        <div className={`risk-score-card ${getHighlightClass('initial_impact')}`}>
          <div className="risk-label">Impact</div>
          <div className={getImpactColor(form.initial_impact)}>{form.initial_impact || 'N/A'}</div>
        </div>
      </div>

      <div className={`risk-reason-card ${getHighlightClass('severity_reason')}`}>
        <div className="risk-label" style={{ display: 'flex', alignItems: 'center' }}>
          Severity Reason
          {ui.statusBadge === 'Ready for Review' && form.severity_reason && <span className="field-status ai-suggested" style={{ marginLeft: 'auto' }}><Sparkles size={12} /> AI Suggested</span>}
        </div>
        <p>{form.severity_reason || 'N/A'}</p>
      </div>

      <div className={`risk-action-card ${getHighlightClass('suggested_next_action')}`}>
        <div className="risk-label" style={{ display: 'flex', alignItems: 'center' }}>
          Suggested Next Action
          {ui.statusBadge === 'Ready for Review' && form.suggested_next_action && <span className="field-status ai-suggested" style={{ marginLeft: 'auto' }}><Sparkles size={12} /> AI Suggested</span>}
        </div>
        <p>{form.suggested_next_action || 'N/A'}</p>
      </div>
    </div>
  );
};
