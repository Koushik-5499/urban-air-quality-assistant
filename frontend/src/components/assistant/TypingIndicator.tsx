export function TypingIndicator() {
  return (
    <div
      className="flex items-center gap-1.5 px-4 py-3 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 w-fit shadow-xs animate-in fade-in duration-200"
      role="status"
      aria-label="Assistant is generating response"
    >
      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-bounce [animation-delay:-0.3s]" />
      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-bounce [animation-delay:-0.15s]" />
      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-bounce" />
      <span className="text-xs text-slate-400 font-medium ml-1.5">Analyzing atmospheric data...</span>
    </div>
  );
}

