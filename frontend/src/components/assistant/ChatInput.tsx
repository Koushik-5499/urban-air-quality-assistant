import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { Send, CornerDownLeft } from 'lucide-react';
import { Button } from '../ui/Button';

export interface ChatInputProps {
  onSendMessage: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSendMessage,
  disabled = false,
  placeholder = 'Ask about AQI conditions, exercise safety, PM2.5, or health advice...',
}: ChatInputProps) {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [text]);

  const handleSubmit = () => {
    if (!text.trim() || disabled) return;
    onSendMessage(text);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.focus();
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const isValid = text.trim().length > 0;

  return (
    <div className="p-3 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-sm transition-all focus-within:ring-2 focus-within:ring-emerald-500/40 focus-within:border-emerald-500">
      <div className="flex items-end gap-2">
        <textarea
          id="chat-input-textarea"
          name="chat-input"
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="flex-1 max-h-28 py-1.5 px-2 text-xs bg-transparent text-slate-900 dark:text-white placeholder:text-slate-400 resize-none focus:outline-none leading-relaxed"
          aria-label="Message input for AI Health Assistant"
        />

        <Button
          variant="primary"
          size="sm"
          onClick={handleSubmit}
          disabled={!isValid || disabled}
          className="shrink-0 text-xs px-3 py-1.5"
          aria-label="Send message"
        >
          <Send className="w-3.5 h-3.5 mr-1" />
          <span>Send</span>
        </Button>
      </div>

      <div className="flex items-center justify-between pt-2 px-1 text-[10px] text-slate-400 border-t border-slate-100 dark:border-slate-800/80 mt-2">
        <span className="flex items-center gap-1">
          <CornerDownLeft className="w-3 h-3 text-slate-400" />
          Press <strong>Enter</strong> to send, <strong>Shift + Enter</strong> for a new line
        </span>
        <span>{text.length} characters</span>
      </div>
    </div>
  );
}
