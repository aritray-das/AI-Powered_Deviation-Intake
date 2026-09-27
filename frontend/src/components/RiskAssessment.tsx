
import { useSelector } from 'react-redux';
import type { RootState } from '../store/store';
import { ShieldAlert, Sparkles } from 'lucide-react';

export const RiskAssessment: React.FC = () => {
  const form = useSelector((state: RootState) => state.deviation.form);
  const ui = useSelector((state: RootState) => state.deviation.ui);
  const { fieldsRecentlyChanged } = ui;

  const getHighlightClass = (field: string) => 
    fieldsRecentlyChanged.includes(field) ? 'field-highlight' : '';

  return (
    <div className="risk-assessment-box">
      <h3><ShieldAlert size={18} color="#2563eb" /> AI Risk Assessment</h3>
      <div className={`read-only-field ${getHighlightClass('severity_reason')}`}>
        <label style={{ display: 'flex', alignItems: 'center' }}>
          Severity Reason
          {ui.statusBadge === 'Ready for Review' && form.severity_reason && <span className="field-status ai-suggested"><Sparkles size={12} /> AI Suggested</span>}
        </label>
        <p>{form.severity_reason || 'N/A'}</p>
      </div>
      <div className={`read-only-field ${getHighlightClass('suggested_next_action')}`}>
        <label style={{ display: 'flex', alignItems: 'center' }}>
          Suggested Next Action
          {ui.statusBadge === 'Ready for Review' && form.suggested_next_action && <span className="field-status ai-suggested"><Sparkles size={12} /> AI Suggested</span>}
        </label>
        <p>{form.suggested_next_action || 'N/A'}</p>
      </div>
      <div className={`read-only-field ${getHighlightClass('ai_confidence')}`}>
        <label style={{ display: 'flex', alignItems: 'center' }}>AI Confidence Score</label>
        <div>
          {form.ai_confidence !== null ? (
            <span className="confidence-badge">{(form.ai_confidence * 100).toFixed(0)}%</span>
          ) : 'N/A'}
        </div>
      </div>
    </div>
  );
};
