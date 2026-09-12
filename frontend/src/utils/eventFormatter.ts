/**
 * Centralized formatting and presentation mapping for backend simulation events.
 * Converts raw backend envelopes and payloads into accessible, human-readable event items.
 */
import { COUNTRY_GEO_REGISTRY } from './geoCoordinates';

export type EventSeverity = 'critical' | 'warning' | 'info' | 'success' | 'neutral';

export interface FormattedEvent {
  id: string;
  eventType: string;
  category: 'crisis' | 'decision' | 'negotiation' | 'system' | 'general';
  title: string;
  description: string;
  tick: number;
  timeDisplay: string;
  actor?: {
    id?: string;
    name: string;
    flag?: string;
  };
  severity: EventSeverity;
  ragCitation?: string;
  rawPayload: Record<string, unknown>;
}

export function formatSimulationEvent(
  rawEvent: Record<string, unknown>,
  indexFallback = 0
): FormattedEvent {
  const eventId = String(rawEvent.event_id || `evt_${Date.now()}_${indexFallback}`);
  const eventType = String(rawEvent.event_type || rawEvent.type || 'SYSTEM_EVENT').toUpperCase();
  const tick = typeof rawEvent.tick === 'number' ? rawEvent.tick : (typeof rawEvent.time_offset === 'number' ? rawEvent.time_offset : 0);
  const timeDisplay = String(rawEvent.timestamp || `T+${String(tick).padStart(2, '0')}`);

  const payload = (typeof rawEvent.payload === 'object' && rawEvent.payload !== null
    ? rawEvent.payload
    : {}) as Record<string, unknown>;

  // Detect actor (country or coordinator)
  const countryId = String(payload.country_id || rawEvent.country_id || '');
  let actor: FormattedEvent['actor'] | undefined;

  if (countryId && COUNTRY_GEO_REGISTRY[countryId]) {
    actor = {
      id: countryId,
      name: String(payload.country_name || payload.name || COUNTRY_GEO_REGISTRY[countryId].name),
      flag: COUNTRY_GEO_REGISTRY[countryId].flag,
    };
  } else if (countryId) {
    actor = {
      id: countryId,
      name: String(payload.country_name || payload.name || countryId),
      flag: '🌐',
    };
  } else if (
    eventType.includes('COORDINATOR') ||
    eventType.includes('NEGOTIATION') ||
    eventType.includes('PROPOSAL')
  ) {
    actor = {
      name: 'International Coordinator',
      flag: '🏛️',
    };
  }

  // Detect RAG citation
  let ragCitation: string | undefined;
  if (Array.isArray(payload.rag_sources) && payload.rag_sources.length > 0) {
    ragCitation = String(payload.rag_sources[0]);
  } else if (payload.rag_grounded && payload.source_framework) {
    ragCitation = String(payload.source_framework);
  }

  // Format by event type
  switch (eventType) {
    case 'CRISIS_TRIGGERED':
    case 'CRISIS_EVENT_TRIGGERED':
    case 'CRISIS_ESCALATION':
      return {
        id: eventId,
        eventType,
        category: 'crisis',
        title: String(payload.title || 'Crisis Anomaly Triggered'),
        description: String(payload.description || 'Emergency AI crisis escalation reported across multilateral networks.'),
        tick,
        timeDisplay,
        actor,
        severity: 'critical',
        ragCitation,
        rawPayload: payload,
      };

    case 'POLICY_ACTION':
    case 'DECISION_RECORDED':
    case 'COUNTRY_DECISION':
      return {
        id: eventId,
        eventType,
        category: 'decision',
        title: String(payload.label || payload.action_name || 'Policy Action Committed'),
        description: String(payload.reasoning || payload.description || 'National authority dispatched autonomous response action.'),
        tick,
        timeDisplay,
        actor,
        severity: 'info',
        ragCitation,
        rawPayload: payload,
      };

    case 'COUNTRY_STATUS_CHANGED':
    case 'COUNTRY_STATE_UPDATED':
    case 'COUNTRY_NOTIFICATION':
      return {
        id: eventId,
        eventType,
        category: 'general',
        title: `${actor?.name || 'Country'} Status: ${String(payload.status || 'Updated')}`,
        description: `Operational awareness shifted to ${String(payload.status || 'Investigating')}. Tension index at ${payload.tension_level ?? 'nominal'}%.`,
        tick,
        timeDisplay,
        actor,
        severity: payload.status === 'Coordinating' ? 'success' : payload.status === 'Investigating' ? 'warning' : 'info',
        ragCitation,
        rawPayload: payload,
      };

    case 'COORDINATOR_PROPOSAL':
      return {
        id: eventId,
        eventType,
        category: 'negotiation',
        title: String(payload.title || 'Multilateral Treaty Proposed'),
        description: String(payload.summary || payload.rationale || 'International Coordinator presented emergency mitigation framework for multilateral voting.'),
        tick,
        timeDisplay,
        actor,
        severity: 'warning',
        ragCitation,
        rawPayload: payload,
      };

    case 'NEGOTIATION_STARTED':
    case 'NEGOTIATION_ROUND_COMPLETED':
    case 'NEGOTIATION_OUTCOME':
    case 'NEGOTIATION_PASSED':
      return {
        id: eventId,
        eventType,
        category: 'negotiation',
        title: String(payload.headline || `Negotiation ${eventType.replace(/_/g, ' ')}`),
        description: String(payload.message || payload.outcome || 'Diplomatic voting round concluded among member nations.'),
        tick,
        timeDisplay,
        actor,
        severity: eventType.includes('PASSED') ? 'success' : 'info',
        ragCitation,
        rawPayload: payload,
      };

    case 'TICK_ADVANCED':
    case 'STEP_COMPLETED':
      return {
        id: eventId,
        eventType,
        category: 'system',
        title: `Simulation Clock: Tick ${tick}`,
        description: `Timeline advanced to ${timeDisplay}. Multi-agent telemetry synchronized.`,
        tick,
        timeDisplay,
        severity: 'neutral',
        rawPayload: payload,
      };

    case 'SIMULATION_STARTED':
      return {
        id: eventId,
        eventType,
        category: 'system',
        title: 'Simulation Initialized & Running',
        description: 'Crisis parameters loaded and multi-agent coordination loop active.',
        tick,
        timeDisplay,
        severity: 'success',
        rawPayload: payload,
      };

    case 'SIMULATION_PAUSED':
    case 'SIMULATION_RESUMED':
    case 'SIMULATION_STOPPED':
      return {
        id: eventId,
        eventType,
        category: 'system',
        title: `Execution State: ${eventType.replace(/_/g, ' ')}`,
        description: `Operator command dispatched at ${timeDisplay}.`,
        tick,
        timeDisplay,
        severity: 'neutral',
        rawPayload: payload,
      };

    default:
      // Graceful fallback for any unknown or future event types
      return {
        id: eventId,
        eventType,
        category: 'general',
        title: String(payload.title || eventType.replace(/_/g, ' ')),
        description: String(payload.description || payload.message || payload.detail || JSON.stringify(payload)),
        tick,
        timeDisplay,
        actor,
        severity: 'info',
        ragCitation,
        rawPayload: payload,
      };
  }
}
