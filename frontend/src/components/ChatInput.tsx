import { useState, useRef } from 'react';

import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from '../store/store';
import { processText, sendEditMessage, extractPdf } from '../store/deviationSlice';
import { Send, Paperclip, X } from 'lucide-react';

export const ChatInput: React.FC = () => {
  const [text, setText] = useState('');
  const [attachment, setAttachment] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dispatch = useDispatch<AppDispatch>();
  const { ui, form } = useSelector((state: RootState) => state.deviation);

  const isFormPopulated = !!form.title || !!form.detailed_description;

  const handleSend = () => {
    if (!text.trim() && !attachment) return;
    
    if (attachment) {
      dispatch(extractPdf(attachment));
      setAttachment(null);
    }
    
    if (text.trim()) {
      if (isFormPopulated) {
        dispatch(sendEditMessage(text.trim()));
      } else {
        dispatch(processText(text.trim()));
      }
      setText('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setAttachment(e.target.files[0]);
    }
    e.target.value = ''; // Reset input
  };

  return (
    <div className="chat-input-container">
      {attachment && (
        <div className="attachment-chip">
          <span className="attachment-name">{attachment.name}</span>
          <button className="attachment-remove" onClick={() => setAttachment(null)}>
            <X size={14} />
          </button>
        </div>
      )}
      <div className="chat-input-wrapper">
        <button 
          className="paperclip-btn-beside"
          onClick={() => fileInputRef.current?.click()}
          disabled={ui.isProcessing || ui.isEditing || ui.isExtracting}
          title="Attach PDF or DOCX file"
        >
          <Paperclip size={20} />
        </button>
        <input 
          type="file" 
          ref={fileInputRef} 
          style={{ display: 'none' }} 
          accept=".pdf,.doc,.docx"
          onChange={handleFileChange} 
        />
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
          disabled={(!text.trim() && !attachment) || ui.isProcessing || ui.isEditing || ui.isExtracting}
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
};
