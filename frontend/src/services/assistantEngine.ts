/**
 * AI Health Assistant Service Facade
 * Delegates query interpretation and synthesized health guidance to specialized sub-modules.
 */
export { SUGGESTED_QUESTIONS, detectQueryTopic } from './assistant/queryParser';
export type { AssistantTopic } from './assistant/queryParser';
export { generateAssistantResponse, getHealthRecommendationsForCity } from './assistant/ruleEngine';
