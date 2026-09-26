
import { useSelector } from 'react-redux';
import type { RootState } from '../store/store';
import { ChatHistory } from './ChatHistory';
import { FileDropzone } from './FileDropzone';
import { ChatInput } from './ChatInput';

export const AssistantPanel: React.FC = () => {
  const { chatHistory, ui } = useSelector((state: RootState) => state.deviation);
  
  // Show dropzone only if chat is just the greeting message
  const showDropzone = chatHistory.length === 1 && !ui.isExtracting && !ui.isProcessing;

  return (
    <div className="right-panel">
      <div className="panel-header" style={{ borderBottom: '1px solid var(--border-color)', backgroundColor: 'white' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600 }}>AI Assistant</h2>
      </div>
      
      {ui.error && (
        <div className="error-banner">
          {ui.error}
        </div>
      )}

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: showDropzone ? '1.5rem' : 0 }}>
        {showDropzone && <FileDropzone />}
        <ChatHistory />
      </div>
      
      <ChatInput />
    </div>
  );
};
