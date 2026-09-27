import { useCallback } from 'react';

import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from '../store/store';
import { extractPdf } from '../store/deviationSlice';
import { UploadCloud } from 'lucide-react';

export const FileDropzone: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const isExtracting = useSelector((state: RootState) => state.deviation.ui.isExtracting);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (isExtracting) return;
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf') {
        dispatch(extractPdf(file));
      } else {
        alert('Please upload a PDF file.');
      }
    }
  }, [dispatch, isExtracting]);

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      dispatch(extractPdf(e.target.files[0]));
    }
  };

  return (
    <div 
      className="dropzone"
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onClick={() => document.getElementById('pdf-upload')?.click()}
    >
      <UploadCloud size={32} color="#94a3b8" />
      <div>
        <strong>Drag and drop a PDF here</strong>
        <p style={{ fontSize: '0.875rem', marginTop: '0.25rem' }}>or click to browse</p>
      </div>
      <input 
        type="file" 
        id="pdf-upload" 
        accept="application/pdf" 
        style={{ display: 'none' }} 
        onChange={handleFileChange}
      />
    </div>
  );
};
