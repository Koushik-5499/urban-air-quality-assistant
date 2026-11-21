export type MessageSender = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  sender: MessageSender;
  text: string;
  timestamp: string;
  cityContext?: {
    city: string;
    aqi: number;
    category: string;
  };
}

export type HealthSeverity = 'low' | 'moderate' | 'high' | 'severe';

export interface HealthRecommendationCard {
  id: string;
  category: 'activity' | 'masks' | 'ventilation' | 'vulnerable' | 'general';
  title: string;
  description: string;
  severity: HealthSeverity;
  iconName: string;
  bullets: string[];
}

export interface SuggestedQuestion {
  id: string;
  question: string;
  category: string;
}

