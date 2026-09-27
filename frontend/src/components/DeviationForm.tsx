import { useEffect } from 'react';

import { useSelector, useDispatch } from 'react-redux';
import type { RootState, AppDispatch } from '../store/store';
import { updateFormField, clearFieldsRecentlyChanged, saveDeviation } from '../store/deviationSlice';
import { RiskAssessment } from './RiskAssessment';
import { Save, Sparkles, CheckCircle2 } from 'lucide-react';
import { useState } from 'react';

export const DeviationForm: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { form, ui } = useSelector((state: RootState) => state.deviation);

  const [userReviewedFields, setUserReviewedFields] = useState<string[]>([]);

  // Clear highlight animation after 2 seconds and update reviewed fields
  useEffect(() => {
    if (ui.fieldsRecentlyChanged.length > 0) {
      setUserReviewedFields(prev => {
        const newSet = new Set(prev);
        ui.fieldsRecentlyChanged.forEach(f => newSet.add(f));
        return Array.from(newSet);
      });
      const timer = setTimeout(() => {
        dispatch(clearFieldsRecentlyChanged());
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [ui.fieldsRecentlyChanged, dispatch]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const field = e.target.name;
    dispatch(updateFormField({ field: field as any, value: e.target.value }));
    if (!userReviewedFields.includes(field)) {
      setUserReviewedFields(prev => [...prev, field]);
    }
  };

  const FieldStatus = ({ field }: { field: string }) => {
    if (ui.statusBadge !== 'Ready for Review') return null;
    if (userReviewedFields.includes(field)) {
      return <span className="field-status reviewed"><CheckCircle2 size={12} /> Reviewed</span>;
    }
    if ((form as any)[field]) {
      return <span className="field-status ai-suggested"><Sparkles size={12} /> AI Suggested</span>;
    }
    return null;
  };

  const ExtractionSummary = () => {
    if (ui.statusBadge !== 'Ready for Review') return null;

    const inputKeys = Object.keys(form).filter(
      k => k !== 'ai_confidence' && k !== 'severity_reason' && k !== 'suggested_next_action'
    ) as Array<keyof typeof form>;

    const populatedCount = inputKeys.filter(k => form[k] && !userReviewedFields.includes(k)).length;
    const emptyCount = inputKeys.filter(k => !form[k]).length;
    const reviewedCount = userReviewedFields.filter(k => inputKeys.includes(k as any)).length;

    return (
      <div className="extraction-summary">
        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
          <div className="summary-stat">
            <span className="stat-num ai">{populatedCount}</span>
            <span className="stat-label">AI Populated</span>
          </div>
          <div className="summary-stat">
            <span className="stat-num warning">{emptyCount}</span>
            <span className="stat-label">Empty Fields</span>
          </div>
          <div className="summary-stat">
            <span className="stat-num success">{reviewedCount}</span>
            <span className="stat-label">Reviewed</span>
          </div>
        </div>
        <div className="summary-msg">
          <Sparkles size={14} color="#7e22ce" />
          Review highlighted fields before saving
        </div>
      </div>
    );
  };

  const getHighlightClass = (field: string) =>
    ui.fieldsRecentlyChanged.includes(field) ? 'field-highlight' : '';

  const handleSave = () => {
    dispatch(saveDeviation());
  };

  const isFormEmpty = !form.title && !form.detailed_description;

  return (
    <div className="left-panel">
      <div className="panel-header">
        <div>
          <h1>Log Deviation</h1>
          <div className="panel-subtitle">Record any unexpected event, out-of-specification result or non-conformance.</div>
        </div>
        <span className={`status-badge ${ui.statusBadge.toLowerCase().replace(/ /g, '-')}`}>
          {ui.statusBadge}
        </span>
      </div>

      <div className="form-content">
        <ExtractionSummary />
        <div className="section-divider">
          <span>1. Deviation Information</span>
          <hr />
        </div>

        <div className="form-group">
          <label>Title <FieldStatus field="title" /></label>
          <input
            type="text"
            name="title"
            value={form.title}
            onChange={handleChange}
            className={getHighlightClass('title')}
            placeholder={ui.statusBadge === 'Draft' ? "Awaiting AI extraction..." : "Short description of the deviation..."}
          />
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Site/Plant <FieldStatus field="site_plant" /></label>
            <input
              type="text"
              name="site_plant"
              value={form.site_plant}
              onChange={handleChange}
              className={getHighlightClass('site_plant')}
            />
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Date of Occurrence <FieldStatus field="date_of_occurrence" /></label>
            <input
              type="text"
              name="date_of_occurrence"
              value={form.date_of_occurrence}
              onChange={handleChange}
              className={getHighlightClass('date_of_occurrence')}
              placeholder="e.g. July 15, 2024"
            />
          </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Source <FieldStatus field="source" /></label>
            <select name="source" value={form.source} onChange={handleChange} className={getHighlightClass('source')}>
              <option value="">Select source...</option>
              <option value="Production Floor">Production Floor</option>
              <option value="Laboratory">Laboratory</option>
              <option value="Audit Finding">Audit Finding</option>
              <option value="Regulatory Inspection">Regulatory Inspection</option>
              <option value="Self-Reported">Self-Reported</option>
              <option value="Other">Other</option>
            </select>
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Batch/Lot Number <FieldStatus field="batch_lot_number" /></label>
            <input
              type="text"
              name="batch_lot_number"
              value={form.batch_lot_number}
              onChange={handleChange}
              className={getHighlightClass('batch_lot_number')}
            />
          </div>
        </div>

        <div className="form-group">
          <label>Related Product/Material <FieldStatus field="related_product_material" /></label>
          <input
            type="text"
            name="related_product_material"
            value={form.related_product_material}
            onChange={handleChange}
            className={getHighlightClass('related_product_material')}
          />
        </div>

        <div className="section-divider">
          <span>2. Deviation Details</span>
          <hr />
        </div>

        <div className="form-group">
          <label>Detailed Description <FieldStatus field="detailed_description" /></label>
          <textarea
            name="detailed_description"
            value={form.detailed_description}
            onChange={handleChange}
            className={getHighlightClass('detailed_description')}
            maxLength={2000}
            placeholder={ui.statusBadge === 'Draft' ? "Awaiting AI extraction..." : ""}
          />
          <div className="char-counter">
            {form.detailed_description.length} / 2000
          </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Initial Severity <FieldStatus field="initial_severity" /></label>
            <select name="initial_severity" value={form.initial_severity} onChange={handleChange} className={getHighlightClass('initial_severity')}>
              <option value="">Select...</option>
              <option value="Critical">Critical</option>
              <option value="Major">Major</option>
              <option value="Minor">Minor</option>
            </select>
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Initial Impact <FieldStatus field="initial_impact" /></label>
            <select name="initial_impact" value={form.initial_impact} onChange={handleChange} className={getHighlightClass('initial_impact')}>
              <option value="">Select...</option>
              <option value="Critical Impact">Critical Impact</option>
              <option value="Major Impact">Major Impact</option>
              <option value="Minor Impact">Minor Impact</option>
              <option value="No Impact">No Impact</option>
            </select>
          </div>
        </div>

        <RiskAssessment />
      </div>

      <div className="panel-footer">
        <button
          className="btn-primary"
          onClick={handleSave}
          disabled={ui.isSaving || isFormEmpty}
        >
          {ui.isSaving ? <span className="loading-indicator"></span> : <Save size={18} />}
          {ui.isSaving ? 'Saving...' : 'Save Deviation'}
        </button>
      </div>
    </div>
  );
};
