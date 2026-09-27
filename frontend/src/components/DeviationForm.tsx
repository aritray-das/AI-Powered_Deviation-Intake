import { useEffect } from 'react';

import { useSelector, useDispatch } from 'react-redux';
import type { RootState, AppDispatch } from '../store/store';
import { updateFormField, clearFieldsRecentlyChanged, saveDeviation } from '../store/deviationSlice';
import { RiskAssessment } from './RiskAssessment';
import { Save } from 'lucide-react';

export const DeviationForm: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { form, ui } = useSelector((state: RootState) => state.deviation);

  // Clear highlight animation after 2 seconds
  useEffect(() => {
    if (ui.fieldsRecentlyChanged.length > 0) {
      const timer = setTimeout(() => {
        dispatch(clearFieldsRecentlyChanged());
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [ui.fieldsRecentlyChanged, dispatch]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    dispatch(updateFormField({ field: e.target.name as any, value: e.target.value }));
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
        <div className="section-divider">
          <span>1. Deviation Information</span>
          <hr />
        </div>

        <div className="form-group">
          <label>Title</label>
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
            <label>Site/Plant</label>
            <input 
              type="text" 
              name="site_plant" 
              value={form.site_plant} 
              onChange={handleChange}
              className={getHighlightClass('site_plant')}
            />
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Date of Occurrence</label>
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
            <label>Source</label>
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
            <label>Batch/Lot Number</label>
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
          <label>Related Product/Material</label>
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
          <label>Detailed Description</label>
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
            <label>Initial Severity</label>
            <select name="initial_severity" value={form.initial_severity} onChange={handleChange} className={getHighlightClass('initial_severity')}>
              <option value="">Select...</option>
              <option value="Critical">Critical</option>
              <option value="Major">Major</option>
              <option value="Minor">Minor</option>
            </select>
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label>Initial Impact</label>
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
