import { useEffect, useRef } from 'react';

import { useSelector, useDispatch } from 'react-redux';
import type { RootState, AppDispatch } from '../store/store';
import { processText } from '../store/deviationSlice';
import { Sparkles, Bot, User } from 'lucide-react';

export const ChatHistory: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { chatHistory, ui } = useSelector((state: RootState) => state.deviation);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, ui.isProcessing, ui.isEditing, ui.isExtracting]);

  const handleProcessAi = (text: string) => {
    dispatch(processText(text));
  };

  return (
    <div className="chat-history">
      {chatHistory.map((msg) => (
        <div key={msg.id} className={`message ${msg.role}`}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 500, fontSize: '0.85rem', opacity: 0.8 }}>
            {msg.role === 'assistant' ? <><Bot size={14} /> AI Assistant</> : <><User size={14} /> You</>}
          </div>
          {msg.content}
          
          {msg.type === 'extracted_text_preview' && msg.rawText && (
            <>
              <div className="extracted-preview">
                {msg.rawText}
              </div>
              <button 
                className="process-btn"
                onClick={() => handleProcessAi(msg.rawText!)}
                disabled={ui.isProcessing}
              >
                <Sparkles size={16} />
                Process with AI
              </button>
            </>
          )}
        </div>
      ))}
      
      {(ui.isProcessing || ui.isEditing || ui.isExtracting) && (
        <div className="message assistant">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 500, fontSize: '0.85rem', opacity: 0.8 }}>
             <Bot size={14} /> AI Assistant
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.5rem' }}>
            <span className="loading-indicator dark"></span>
            {ui.isExtracting ? 'Analyzing document...' : ui.isProcessing ? 'Processing deviation...' : 'Applying edit...'}
          </div>
        </div>
      )}
      <div ref={endOfMessagesRef} />
    </div>
  );
};
