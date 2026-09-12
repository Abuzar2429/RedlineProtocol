import React, { useState, useMemo } from 'react';
import {
  Clock,
  Filter,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { useSimulationStore } from '../../stores/simulationStore';
import { formatSimulationEvent, type FormattedEvent } from '../../utils/eventFormatter';
import { TimelineEventCard } from './TimelineEventCard';

type TimelineFilter = 'all' | 'crisis' | 'negotiation' | 'decision' | 'system';

export const SimulationTimeline: React.FC = () => {
  const currentTick = useSimulationStore((s) => s.currentTick);
  const status = useSimulationStore((s) => s.status);
  const eventHistory = useSimulationStore((s) => s.eventHistory);
  const events = useSimulationStore((s) => s.events);
  const decisions = useSimulationStore((s) => s.decisions);
  const proposals = useSimulationStore((s) => s.proposals);

  const [activeFilter, setActiveFilter] = useState<TimelineFilter>('all');

  // Authoritative deduplication and chronological ordering
  const formattedEvents = useMemo<FormattedEvent[]>(() => {
    const rawList: Record<string, unknown>[] = [];
    const seenIds = new Set<string>();

    // 1. Ingest eventHistory (or events fallback)
    const sourceEvents = eventHistory.length > 0 ? eventHistory : events;
    for (const ev of sourceEvents) {
      if (ev && ev.event_id && !seenIds.has(ev.event_id)) {
        seenIds.add(ev.event_id);
        rawList.push(ev as unknown as Record<string, unknown>);
      }
    }

    // 2. Ingest decisions if not already recorded in events
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

    // 3. Ingest proposals if not already recorded
    for (const prop of proposals) {
      const pid = prop.proposal_id || `prop_${prop.round}`;
      if (!seenIds.has(pid)) {
        seenIds.add(pid);
        rawList.push({
          event_id: pid,
          event_type: 'COORDINATOR_PROPOSAL',
          tick: prop.tick,
          timestamp: `T+${String(prop.tick).padStart(2, '0')}`,
          payload: prop,
        });
      }
    }

    // 4. Format all items safely
    const formatted = rawList.map((item, idx) => formatSimulationEvent(item, idx));

    // 5. Authoritative sorting: strictly by virtual simulation tick (ascending T0 -> T+04 -> ...)
    formatted.sort((a, b) => a.tick - b.tick);

    return formatted;
  }, [eventHistory, events, decisions, proposals]);

  // Filtered event list
  const filteredEvents = useMemo(() => {
    if (activeFilter === 'all') return formattedEvents;
    return formattedEvents.filter((ev) => ev.category === activeFilter);
  }, [formattedEvents, activeFilter]);

  // Group events by tick for timeline progression visualization
  const groupedByTick = useMemo(() => {
    const map = new Map<number, FormattedEvent[]>();
    for (const ev of filteredEvents) {
      const list = map.get(ev.tick) || [];
      list.push(ev);
      map.set(ev.tick, list);
    }
    return Array.from(map.entries()).sort(([tickA], [tickB]) => tickA - tickB);
  }, [filteredEvents]);

  return (
    <div
      data-testid="simulation-timeline"
      className="rounded-2xl border border-slate-800 bg-slate-900/80 backdrop-blur-md p-4 flex flex-col shadow-lg space-y-4"
    >
      {/* Header: Title + Current Virtual Tick Indicator + Filters */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between pb-3 border-b border-slate-800 gap-3">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-slate-800/80 border border-slate-700/60 text-cyan-400">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider font-mono">
                Crisis Progression Timeline
              </h2>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {filteredEvents.length} Events Recorded
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Authoritative Virtual Simulation Time • Spec §6.4
            </p>
          </div>
        </div>

        {/* Current Position Marker + Filter Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Current Simulation Tick Anchor */}
          <div
            data-testid="timeline-current-position"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-cyan-950/80 border border-cyan-800 font-mono text-xs font-bold text-cyan-300 shadow-sm"
          >
            <Clock className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            <span>CURRENT: T+{String(currentTick).padStart(2, '0')}</span>
            <span className="text-cyan-700">|</span>
            <span className="text-[10px] text-cyan-400 font-normal uppercase">{status}</span>
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center space-x-1 bg-slate-950/60 p-1 rounded-lg border border-slate-800 text-xs font-mono">
            <Filter className="w-3 h-3 text-slate-500 ml-1 mr-0.5" />
            {(['all', 'crisis', 'negotiation', 'decision', 'system'] as TimelineFilter[]).map(
              (cat) => (
                <button
                  key={cat}
                  onClick={() => setActiveFilter(cat)}
                  className={`px-2 py-0.5 rounded transition-colors uppercase text-[10px] font-semibold cursor-pointer ${
                    activeFilter === cat
                      ? 'bg-slate-800 text-cyan-300 font-bold'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {cat}
                </button>
              )
            )}
          </div>
        </div>
      </div>

      {/* Timeline Event Feed / Container */}
      {groupedByTick.length === 0 ? (
        <div
          data-testid="simulation-timeline-empty"
          className="p-8 text-center flex flex-col items-center justify-center rounded-xl bg-slate-950/40 border border-dashed border-slate-800"
        >
          <Clock className="w-8 h-8 text-slate-600 mb-2" />
          <h4 className="text-xs font-semibold text-slate-300 mb-1">No Timeline Events Recorded</h4>
          <p className="text-xs text-slate-500 max-w-sm">
            Step or run the simulation engine to generate authoritative multi-agent decisions, proposals, and crisis escalations.
          </p>
        </div>
      ) : (
        <div className="relative overflow-x-auto overflow-y-hidden pb-3 pt-1">
          {/* Horizontal / Flowing Timeline */}
          <div className="flex items-start space-x-6 min-w-max px-2">
            {groupedByTick.map(([tick, tickEvents]) => {
              const isCurrentTick = tick === currentTick;
              return (
                <div
                  key={tick}
                  className={`relative flex flex-col space-y-2 min-w-[280px] max-w-[320px] ${
                    isCurrentTick ? 'opacity-100' : 'opacity-90'
                  }`}
                >
                  {/* Tick Node Header */}
                  <div className="flex items-center space-x-2">
                    <div
                      className={`w-3.5 h-3.5 rounded-full border-2 flex items-center justify-center ${
                        isCurrentTick
                          ? 'border-cyan-400 bg-cyan-500 shadow-md shadow-cyan-500/50'
                          : 'border-slate-600 bg-slate-900'
                      }`}
                    >
                      {isCurrentTick && <div className="w-1.5 h-1.5 rounded-full bg-slate-950" />}
                    </div>
                    <span
                      className={`font-mono text-xs font-bold ${
                        isCurrentTick ? 'text-cyan-300' : 'text-slate-300'
                      }`}
                    >
                      T+{String(tick).padStart(2, '0')}
                    </span>
                    <div className="h-px flex-1 bg-slate-800" />
                    <ArrowRight className="w-3 h-3 text-slate-600" />
                  </div>

                  {/* Event cards under this tick */}
                  <div className="space-y-2 pl-4 border-l border-slate-800/80">
                    {tickEvents.map((ev) => (
                      <TimelineEventCard
                        key={ev.id}
                        event={ev}
                        isCurrent={isCurrentTick}
                      />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
