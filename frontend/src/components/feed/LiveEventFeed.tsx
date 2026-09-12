import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Radio, ArrowDown, WifiOff } from 'lucide-react';
import { useSimulationStore } from '../../stores/simulationStore';
import { useConnectionStore } from '../../stores/connectionStore';
import { formatSimulationEvent, type FormattedEvent } from '../../utils/eventFormatter';
import { EventCard } from './EventCard';
import { EmptyState } from '../feedback/EmptyState';

type FilterCategory = 'all' | 'decision' | 'crisis' | 'negotiation';

export const LiveEventFeed: React.FC = () => {
  const [filter, setFilter] = useState<FilterCategory>('all');
  const [autoScroll, setAutoScroll] = useState<boolean>(true);

  const eventHistory = useSimulationStore((s) => s.eventHistory);
  const events = useSimulationStore((s) => s.events);
  const decisions = useSimulationStore((s) => s.decisions);
  const connectionState = useConnectionStore((s) => s.state);

  const feedContainerRef = useRef<HTMLDivElement>(null);
  const isUserScrollingRef = useRef<boolean>(false);

  // Combine and deduplicate events from store, maintaining backend ordering
  const formattedEvents = useMemo<FormattedEvent[]>(() => {
    const rawList: Record<string, unknown>[] = [];
    const seenIds = new Set<string>();

    // 1. Ingest eventHistory (or events)
    const sourceEvents = eventHistory.length > 0 ? eventHistory : events;
    for (const ev of sourceEvents) {
      if (ev && ev.event_id && !seenIds.has(ev.event_id)) {
        seenIds.add(ev.event_id);
        rawList.push(ev as unknown as Record<string, unknown>);
      }
    }

    // 2. Ingest decisions as events if not already present
    for (const dec of decisions) {
      if (dec && dec.decision_id && !seenIds.has(dec.decision_id)) {
        seenIds.add(dec.decision_id);
        rawList.push({
          event_id: dec.decision_id,
          event_type: 'DECISION_RECORDED',
          tick: dec.tick,
          timestamp: `T+${String(dec.tick).padStart(2, '0')}`,
          payload: dec,
        });
      }
    }

    // 3. Format and sort according to backend tick and sequence
    const formatted = rawList.map((item, idx) => formatSimulationEvent(item, idx));

    // Sort chronologically (T+00 -> T+01 -> ...)
    formatted.sort((a, b) => a.tick - b.tick);

    return formatted;
  }, [eventHistory, events, decisions]);

  // Apply Category Filter
  const filteredEvents = useMemo(() => {
    if (filter === 'all') return formattedEvents;
    return formattedEvents.filter((ev) => ev.category === filter);
  }, [formattedEvents, filter]);

  // Handle Scroll to detect if user manually scrolled up
  const handleScroll = () => {
    if (!feedContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = feedContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;

    if (!isAtBottom && autoScroll) {
      setAutoScroll(false);
    } else if (isAtBottom && !autoScroll && !isUserScrollingRef.current) {
      setAutoScroll(true);
    }
  };

  // Auto-scroll when new events arrive IF autoScroll is enabled
  useEffect(() => {
    if (!autoScroll || !feedContainerRef.current) return;
    const el = feedContainerRef.current;
    if (typeof el.scrollTo === 'function') {
      el.scrollTo({
        top: el.scrollHeight,
        behavior: 'smooth',
      });
    } else {
      el.scrollTop = el.scrollHeight;
    }
  }, [filteredEvents.length, autoScroll]);

  const scrollToBottom = () => {
    if (!feedContainerRef.current) return;
    const el = feedContainerRef.current;
    if (typeof el.scrollTo === 'function') {
      el.scrollTo({
        top: el.scrollHeight,
        behavior: 'smooth',
      });
    } else {
      el.scrollTop = el.scrollHeight;
    }
    setAutoScroll(true);
  };

  return (
    <div
      role="region"
      aria-label="Live Crisis Event Feed"
      className="flex flex-col h-[460px] lg:h-[540px] rounded-xl border border-slate-800 bg-slate-950 shadow-inner overflow-hidden"
    >
      {/* Header Bar */}
      <div className="p-3 border-b border-slate-800 bg-slate-900/60 backdrop-blur flex items-center justify-between shrink-0">
        <div className="flex items-center space-x-2">
          <div className="p-1 rounded bg-cyan-950 border border-cyan-800 text-cyan-400">
            <Radio className="w-4 h-4 animate-pulse" />
          </div>
          <div>
            <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-100">
              Live Multilateral Feed
            </h3>
            <span className="text-[10px] text-slate-400">
              {filteredEvents.length} events logged
            </span>
          </div>
        </div>

        {/* Follow Live Button */}
        {!autoScroll && (
          <button
            onClick={scrollToBottom}
            className="flex items-center space-x-1 px-2 py-1 rounded bg-cyan-950/80 border border-cyan-700 text-cyan-300 text-[10px] font-mono hover:bg-cyan-900 transition-colors cursor-pointer animate-bounce"
          >
            <ArrowDown className="w-3 h-3" />
            <span>Follow Live</span>
          </button>
        )}
      </div>

      {/* Filter Tabs */}
      <div className="px-3 py-1.5 border-b border-slate-800 bg-slate-950/80 flex items-center space-x-1 overflow-x-auto text-[10px] font-mono shrink-0">
        {(['all', 'decision', 'crisis', 'negotiation'] as FilterCategory[]).map((cat) => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            className={`px-2 py-1 rounded capitalize transition-colors cursor-pointer ${
              filter === cat
                ? 'bg-cyan-950 text-cyan-300 border border-cyan-800 font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Disconnected Warning Banner */}
      {connectionState !== 'CONNECTED' && (
        <div className="px-3 py-1.5 bg-amber-950/40 border-b border-amber-800/60 flex items-center space-x-2 text-[10px] text-amber-400 shrink-0 font-mono">
          <WifiOff className="w-3.5 h-3.5" />
          <span>WebSocket disconnected ({connectionState}). Stream paused.</span>
        </div>
      )}

      {/* Event Cards Stream */}
      <div
        ref={feedContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-3 space-y-2.5"
      >
        {filteredEvents.length === 0 ? (
          <div className="h-full flex items-center justify-center p-4">
            <EmptyState
              title="No Events Recorded Yet"
              message="Advance the simulation engine using the Step or Run buttons to observe real-time multi-agent decisions."
            />
          </div>
        ) : (
          filteredEvents.map((ev) => <EventCard key={ev.id} event={ev} />)
        )}
      </div>
    </div>
  );
};
