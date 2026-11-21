import { Sparkles } from 'lucide-react';
import type { SuggestedQuestion } from '../../types/assistant';

export interface ChatSuggestedQuestionsProps {
  questions: SuggestedQuestion[];
  onSelectQuestion: (question: string) => void;
  disabled?: boolean;
}

export function ChatSuggestedQuestions({
  questions,
  onSelectQuestion,
  disabled = false,
}: ChatSuggestedQuestionsProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 dark:text-slate-400">
        <Sparkles className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
        <span>Suggested Questions:</span>
      </div>

      <div className="flex flex-wrap gap-2">
        {questions.map((sq) => (
          <button
            key={sq.id}
            type="button"
            disabled={disabled}
            onClick={() => onSelectQuestion(sq.question)}
            className="px-3 py-1.5 rounded-xl text-xs font-medium bg-slate-100 hover:bg-emerald-50 text-slate-700 hover:text-emerald-800 dark:bg-slate-800 dark:hover:bg-emerald-950/50 dark:text-slate-300 dark:hover:text-emerald-300 border border-slate-200/80 dark:border-slate-700 transition-all text-left cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-2xs"
          >
            {sq.question}
          </button>
        ))}
      </div>
    </div>
  );
}

