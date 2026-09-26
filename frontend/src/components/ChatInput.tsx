import { useState } from 'react';

import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from '../store/store';
import { processText, sendEditMessage } from '../store/deviationSlice';
import { Send } from 'lucide-react';

export const ChatInput: React.FC = () => {
  const [text, setText] = useState('');
  const dispatch = useDispatch<AppDispatch>();
  const { ui, form } = useSelector((state: RootState) => state.deviation);

  const isFormPopulated = !!form.title || !!form.detailed_description;

  const handleSend = () => {
    if (!text.trim()) return;
    
    if (isFormPopulated) {
      dispatch(sendEditMessage(text.trim()));
    } else {
      dispatch(processText(text.trim()));
    }
    setText('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-input-container">
      <div className="chat-input-wrapper">
        <textarea
          placeholder={isFormPopulated ? "Type a correction (e.g. 'Actually batch is X')..." : "Paste deviation text here..."}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={ui.isProcessing || ui.isEditing || ui.isExtracting}
        />
        <button 
          className="send-btn" 
          onClick={handleSend}
          disabled={!text.trim() || ui.isProcessing || ui.isEditing || ui.isExtracting}
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
};
