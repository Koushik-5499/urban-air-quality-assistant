export type MessageSender = 'user' | 'assistant' | 'system';

export interface AdviceExplanation {
  priority: string;
  targetGroup: string;
  reason: string;
  supportingSource: string;
}

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
  provenance?: 'gemini' | 'offline_rules';
  explainability?: AdviceExplanation;
}

export type HealthSeverity = 'low' | 'moderate' | 'high' | 'severe';

export interface HealthRecommendationCard {
  id: string;
  category: 'activity' | 'masks' | 'ventilation' | 'vulnerable' | 'general' | 'winter_smog' | 'low_emission' | 'indoor_hack' | 'sustainable';
  title: string;
  description: string;
  severity: HealthSeverity;
  iconName: string;
  bullets: string[];
  impactExplanation?: string;
}

export interface SuggestedQuestion {
  id: string;
  question: string;
  category: string;
}

