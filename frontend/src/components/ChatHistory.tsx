import { useEffect, useRef, useState } from 'react';

import { useSelector, useDispatch } from 'react-redux';
import type { RootState, AppDispatch } from '../store/store';
import { processText } from '../store/deviationSlice';
import { Sparkles, Bot, User, CheckCircle, CircleDashed, Loader2 } from 'lucide-react';

const ProcessingStatus = ({ isProcessing, isExtracting, isEditing }: { isProcessing: boolean, isExtracting: boolean, isEditing: boolean }) => {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (!isProcessing) {
      setStep(0);
      return;
    }
    const t1 = setTimeout(() => setStep(1), 1200);
    const t2 = setTimeout(() => setStep(2), 2400);
    const t3 = setTimeout(() => setStep(3), 3600);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, [isProcessing]);

  if (!isProcessing && !isExtracting && !isEditing) return null;

  return (
    <div className="message assistant">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 500, fontSize: '0.85rem', opacity: 0.8, marginBottom: '0.75rem' }}>
        <Bot size={14} /> AI Assistant
      </div>
      
      {isExtracting && (
        <div className="proc-step active">
          <Loader2 size={16} className="spinner" color="#2563eb" />
          <span>Analyzing document...</span>
        </div>
      )}

      {isEditing && (
        <div className="proc-step active">
          <Loader2 size={16} className="spinner" color="#2563eb" />
          <span>Applying edit...</span>
        </div>
      )}

      {isProcessing && (
        <div className="processing-steps-col">
          {['Reading input', 'Extracting deviation fields', 'Assessing risk', 'Ready for review'].map((s, i) => {
            const isActive = i === step;
            const isDone = i < step;
            const isPending = i > step;
            
            return (
              <div key={s} className={`proc-step ${isActive ? 'active' : ''} ${isDone ? 'done' : ''} ${isPending ? 'pending' : ''}`}>
                {isDone ? (
                  <CheckCircle size={16} color="#16a34a" />
                ) : isActive ? (
                  <Loader2 size={16} className="spinner" color="#2563eb" />
                ) : (
                  <CircleDashed size={16} color="#cbd5e1" />
                )}
                <span>{s}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

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
    <>
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
      
      <ProcessingStatus 
        isProcessing={ui.isProcessing} 
        isExtracting={ui.isExtracting} 
        isEditing={ui.isEditing} 
      />
      <div ref={endOfMessagesRef} />
    </>
  );
};
