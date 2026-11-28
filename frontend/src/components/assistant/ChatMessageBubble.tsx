import { useState } from 'react';
import { Bot, User, Copy, Check, Sparkles, HelpCircle, ChevronDown, Cpu, BookOpen } from 'lucide-react';
import type { ChatMessage } from '../../types/assistant';
import { Badge } from '../ui/Badge';

export interface ChatMessageBubbleProps {
  message: ChatMessage;
}

export function ChatMessageBubble({ message }: ChatMessageBubbleProps) {
  const [copied, setCopied] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const isUser = message.sender === 'user';
  const isSystem = message.sender === 'system';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard fallback
    }
  };

  // Helper to format basic markdown-like paragraphs and bold text
  const renderFormattedText = (text: string) => {
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      if (!line.trim()) {
        return <div key={idx} className="h-2" />;
      }

      // Check if bullet point
      const isBullet = line.startsWith('• ') || line.startsWith('- ');
      const content = isBullet ? line.slice(2) : line;

      // Simple bold replacement
      const parts = content.split(/(\*\*.*?\*\*)/g);

      const parsedLine = parts.map((part, pIdx) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return (
            <strong key={pIdx} className="font-semibold text-slate-900 dark:text-white">
              {part.slice(2, -2)}
            </strong>
          );
        }
        if (part.startsWith('*') && part.endsWith('*')) {
          return (
            <em key={pIdx} className="italic text-slate-500 dark:text-slate-400 text-[11px]">
              {part.slice(1, -1)}
            </em>
          );
        }
        return part;
      });

      if (isBullet) {
        return (
          <div key={idx} className="flex items-start gap-1.5 pl-2 leading-relaxed">
            <span className="text-emerald-500 font-bold">•</span>
            <span>{parsedLine}</span>
          </div>
        );
      }

      return (
        <p key={idx} className="leading-relaxed">
          {parsedLine}
        </p>
      );
    });
  };

  if (isSystem) {
    return (
      <div className="flex justify-center my-3">
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-[11px] text-slate-500 dark:text-slate-400 border border-slate-200/60 dark:border-slate-700">
          <Sparkles className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
          <span>{message.text}</span>
          <span className="text-[10px] opacity-75 font-mono ml-1">{message.timestamp}</span>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`flex items-start gap-3 my-3 animate-in fade-in duration-200 ${
        isUser ? 'flex-row-reverse' : 'flex-row'
      }`}
    >
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-xs font-bold shadow-2xs ${
          isUser
            ? 'bg-emerald-600 text-white'
            : 'bg-teal-50 text-teal-700 dark:bg-teal-950/80 dark:text-teal-300 border border-teal-200/80 dark:border-teal-800/60'
        }`}
        aria-hidden="true"
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Bubble Container */}
      <div
        className={`relative max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 text-xs shadow-2xs group ${
          isUser
            ? 'bg-emerald-600 text-white rounded-tr-xs'
            : 'bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 border border-slate-200/80 dark:border-slate-800 rounded-tl-xs'
        }`}
      >
        {/* Message Content */}
        {message.sender === 'assistant' && (
          <div className="mb-2 flex items-center gap-1.5 flex-wrap">
            {message.provenance === 'offline_rules' ? (
              <Badge variant="neutral" size="sm" className="flex items-center gap-1 font-medium text-slate-700 dark:text-slate-200">
                <BookOpen className="w-3 h-3 text-amber-600 dark:text-amber-400" aria-hidden="true" />
                <span>Offline guidance (built-in rules) — Deterministic Fallback</span>
              </Badge>
            ) : (
              <Badge variant="info" size="sm" className="flex items-center gap-1 font-medium">
                <Cpu className="w-3 h-3 text-sky-600 dark:text-sky-400" aria-hidden="true" />
                <span>Gemini AI (Google)</span>
              </Badge>
            )}
          </div>
        )}
        <div className="space-y-1">{renderFormattedText(message.text)}</div>

        {/* Explainability Accordion: Why this advice? */}
        {message.sender === 'assistant' && (
          <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800">
            <button
              type="button"
              onClick={() => setShowExplanation(!showExplanation)}
              aria-expanded={showExplanation}
              aria-controls={`explain-${message.id}`}
              className="flex items-center gap-1.5 text-[11px] font-semibold text-teal-700 dark:text-teal-400 hover:text-teal-800 dark:hover:text-teal-300 transition-colors cursor-pointer"
            >
              <HelpCircle className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Why this advice?</span>
              <ChevronDown
                className={`w-3.5 h-3.5 transition-transform duration-200 ${
                  showExplanation ? 'rotate-180' : ''
                }`}
                aria-hidden="true"
              />
            </button>

            {showExplanation && (
              <div
                id={`explain-${message.id}`}
                className="mt-2 p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200/60 dark:border-slate-700/60 space-y-1.5 text-[11px] animate-in fade-in duration-150"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-bold text-slate-700 dark:text-slate-300">Priority:</span>
                  <Badge variant="warning" size="sm">
                    {message.explainability?.priority ??
                      (message.cityContext && message.cityContext.aqi > 150
                        ? 'High Priority Alert'
                        : 'Standard Precaution')}
                  </Badge>
                </div>
                <div>
                  <span className="font-bold text-slate-700 dark:text-slate-300">Target Group:</span>{' '}
                  <span className="text-slate-600 dark:text-slate-400">
                    {message.explainability?.targetGroup ??
                      'Children, elderly, asthmatics, pregnant women, and outdoor commuters'}
                  </span>
                </div>
                <div>
                  <span className="font-bold text-slate-700 dark:text-slate-300">Reason:</span>{' '}
                  <span className="text-slate-600 dark:text-slate-400">
                    {message.explainability?.reason ??
                      'Particulate matter (PM2.5/PM10) triggers respiratory tract inflammation, oxidative stress, and alveolar penetration.'}
                  </span>
                </div>
                <div className="pt-1 border-t border-slate-200/50 dark:border-slate-700/50 text-[10px] text-slate-500 dark:text-slate-400">
                  <span className="font-bold">Supporting Source:</span>{' '}
                  <span>
                    {message.explainability?.supportingSource ??
                      'CPCB National Air Quality Index (NAQI) Standards & WHO Global Air Quality Guidelines (2021)'}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Footer: Timestamp & Copy Button */}
        <div
          className={`flex items-center justify-between gap-3 pt-2 mt-2 border-t text-[10px] ${
            isUser
              ? 'border-emerald-500/50 text-emerald-100'
              : 'border-slate-100 dark:border-slate-800 text-slate-400'
          }`}
        >
          <span className="font-mono">{message.timestamp}</span>

          {!isUser && (
            <button
              type="button"
              onClick={handleCopy}
              className="flex items-center gap-1 hover:text-slate-700 dark:hover:text-slate-200 transition-colors cursor-pointer"
              aria-label="Copy assistant response to clipboard"
            >
              {copied ? (
                <>
                  <Check className="w-3 h-3 text-emerald-500" />
                  <span className="text-emerald-500 font-semibold">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  <span>Copy</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

