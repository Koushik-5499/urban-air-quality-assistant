import { useState, useRef, useEffect, useCallback } from 'react';
import { Bot, MessageSquare, ShieldCheck } from 'lucide-react';
import { useLocation } from '../hooks/useLocation';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { AssistantProfileHeader } from '../components/assistant/AssistantProfileHeader';
import { ChatMessageBubble } from '../components/assistant/ChatMessageBubble';
import { ChatInput } from '../components/assistant/ChatInput';
import { ChatSuggestedQuestions } from '../components/assistant/ChatSuggestedQuestions';
import { TypingIndicator } from '../components/assistant/TypingIndicator';
import { ClearChatModal } from '../components/assistant/ClearChatModal';
import { AssistantContextPanel } from '../components/assistant/AssistantContextPanel';
import {
  generateAssistantResponse,
  SUGGESTED_QUESTIONS,
} from '../services/assistantEngine';
import { healthApi } from '../services/api/healthApi';
import type { ChatMessage } from '../types/assistant';

const STORAGE_KEY_CHAT = 'uaqa_assistant_messages';

export function Assistant() {
  useDocumentTitle('AI Health Assistant — Urban Air Quality Assistant');

  const { selectedCityData, selectedCityId } = useLocation();
  const [isTyping, setIsTyping] = useState(false);
  const [isClearModalOpen, setIsClearModalOpen] = useState(false);
  const [activeMobileTab, setActiveMobileTab] = useState<'chat' | 'health'>('chat');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const prevCityIdRef = useRef<string>(selectedCityId);

  // Helper to construct initial welcome message
  const createWelcomeMessage = useCallback(
    (): ChatMessage => ({
      id: 'welcome-msg',
      sender: 'assistant',
      text:
        `Hello! I am your **Urban Air Quality Health Assistant**.\n\n` +
        `I am currently monitoring atmospheric criteria pollutants for **${selectedCityData.location.city}, ${selectedCityData.location.state}** (AQI **${selectedCityData.aqi} — ${selectedCityData.category}**).\n\n` +
        `Ask me anything about today's air quality, outdoor exercise safety, particulate health risks, masks, or precautions for sensitive groups. You can also pick from the suggested questions below!`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      cityContext: {
        city: selectedCityData.location.city,
        aqi: selectedCityData.aqi,
        category: selectedCityData.category,
      },
    }),
    [selectedCityData]
  );

  // Messages state with localStorage persistence
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY_CHAT);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch {
      // storage unavailable
    }
    return [createWelcomeMessage()];
  });

  // Persist messages
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_CHAT, JSON.stringify(messages));
    } catch {
      // storage error
    }
  }, [messages]);

  // Notice when the active city changes elsewhere in the application
  useEffect(() => {
    if (prevCityIdRef.current !== selectedCityId) {
      prevCityIdRef.current = selectedCityId;
      const systemNotice: ChatMessage = {
        id: `sys-${Date.now()}`,
        sender: 'system',
        text: `Active location context updated to ${selectedCityData.location.city} (AQI ${selectedCityData.aqi} • ${selectedCityData.category})`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, systemNotice]);
    }
  }, [selectedCityId, selectedCityData]);

  // Scroll to bottom when messages update or typing starts
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Handle sending a message with Backend Gemini API integration + graceful fallback
  const handleSendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isTyping) return;

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        sender: 'user',
        text: trimmed,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, userMsg]);
      setIsTyping(true);

      try {
        // Build conversation history for FastAPI Gemini endpoint
        const conversationHistory = messages
          .filter((m) => m.sender === 'user' || m.sender === 'assistant')
          .slice(-6)
          .map((m) => ({
            role: m.sender as 'user' | 'assistant',
            content: m.text,
          }));

        const response = await healthApi.askAssistant({
          city: selectedCityData.location.city,
          question: trimmed,
          conversation_history: conversationHistory,
        });

        let responseText = response.answer;
        if (response.recommendations && response.recommendations.length > 0) {
          responseText +=
            '\n\n**Actionable Recommendations:**\n' +
            response.recommendations.map((r) => `• **${r.title}**: ${r.description}`).join('\n');
        }
        if (response.disclaimer) {
          responseText += `\n\n*${response.disclaimer}*`;
        }

        const assistantMsg: ChatMessage = {
          id: `asst-${Date.now()}`,
          sender: 'assistant',
          text: responseText,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          cityContext: {
            city: selectedCityData.location.city,
            aqi: selectedCityData.aqi,
            category: selectedCityData.category,
          },
        };

        setMessages((prev) => [...prev, assistantMsg]);
      } catch {
        // Graceful fallback to built-in rule engine if backend is offline or errors
        const responseText = generateAssistantResponse(trimmed, selectedCityData);
        const assistantMsg: ChatMessage = {
          id: `asst-${Date.now()}`,
          sender: 'assistant',
          text: responseText,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          cityContext: {
            city: selectedCityData.location.city,
            aqi: selectedCityData.aqi,
            category: selectedCityData.category,
          },
        };

        setMessages((prev) => [...prev, assistantMsg]);
      } finally {
        setIsTyping(false);
      }
    },
    [isTyping, messages, selectedCityData]
  );

  // Clear conversation history
  const handleConfirmClear = () => {
    const freshWelcome = createWelcomeMessage();
    setMessages([freshWelcome]);
    try {
      localStorage.removeItem(STORAGE_KEY_CHAT);
    } catch {
      // storage error
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12 animate-in fade-in duration-300">
      {/* 1. Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-200/80 dark:border-slate-800 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-400 border border-teal-200/60 dark:border-teal-800/60">
              <Bot className="w-5 h-5" aria-hidden="true" />
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              AI Environmental Health Assistant
            </h1>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400 max-w-3xl">
            Context-aware environmental health consultation powered by Google Gemini and CPCB guidelines. Receive immediate guidance on outdoor exertion, particulate exposure thresholds, protective measures, and sensitive group precautions tailored to your active city.
          </p>
        </div>

        {/* Mobile View Switcher (Chat vs Health Context) */}
        <div className="inline-flex lg:hidden p-1 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-semibold self-start">
          <button
            type="button"
            onClick={() => setActiveMobileTab('chat')}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
              activeMobileTab === 'chat'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Chat Session</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveMobileTab('health')}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
              activeMobileTab === 'health'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Health Insights</span>
          </button>
        </div>
      </div>

      {/* 2. Main 2-Column Responsive Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Chat Conversation Window (8 cols) */}
        <div
          className={`lg:col-span-8 space-y-4 ${
            activeMobileTab === 'health' ? 'hidden lg:block' : 'block'
          }`}
        >
          {/* Assistant Profile Header */}
          <AssistantProfileHeader
            cityData={selectedCityData}
            messageCount={messages.length}
            onClearChat={() => setIsClearModalOpen(true)}
          />

          {/* Chat Messages Container */}
          <div
            tabIndex={0}
            role="region"
            aria-label="Conversation with Air Quality Assistant"
            className="p-4 sm:p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs min-h-[460px] max-h-[580px] overflow-y-auto space-y-4 focus:outline-hidden focus:ring-2 focus:ring-teal-500/20"
          >
            {messages.map((message) => (
              <ChatMessageBubble key={message.id} message={message} />
            ))}

            {isTyping && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>

          {/* Suggested Quick Questions */}
          <ChatSuggestedQuestions
            questions={SUGGESTED_QUESTIONS}
            onSelectQuestion={handleSendMessage}
            disabled={isTyping}
          />

          {/* User Input Bar */}
          <ChatInput onSendMessage={handleSendMessage} disabled={isTyping} />
        </div>

        {/* Right Column: Health Context Panel (4 cols) */}
        <div
          className={`lg:col-span-4 ${
            activeMobileTab === 'chat' ? 'hidden lg:block' : 'block'
          }`}
        >
          <AssistantContextPanel cityData={selectedCityData} />
        </div>
      </div>

      {/* Clear Chat Confirmation Modal */}
      <ClearChatModal
        isOpen={isClearModalOpen}
        onClose={() => setIsClearModalOpen(false)}
        onConfirm={handleConfirmClear}
      />
    </div>
  );
}

export default Assistant;
