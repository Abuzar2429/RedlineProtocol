import React from 'react';
import {
  AlertTriangle,
  Radio,
  GitCommit,
  Cpu,
  BookOpen,
  Info,
} from 'lucide-react';
import type { FormattedEvent } from '../../utils/eventFormatter';

interface EventCardProps {
  event: FormattedEvent;
}

export const EventCard: React.FC<EventCardProps> = ({ event }) => {
  const getIcon = () => {
    switch (event.category) {
      case 'crisis':
        return <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />;
      case 'decision':
        return <Cpu className="w-4 h-4 text-cyan-400 shrink-0" />;
      case 'negotiation':
        return <GitCommit className="w-4 h-4 text-amber-400 shrink-0" />;
      case 'system':
        return <Radio className="w-4 h-4 text-slate-400 shrink-0" />;
      default:
        return <Info className="w-4 h-4 text-blue-400 shrink-0" />;
    }
  };

  const getBorderColor = () => {
    switch (event.severity) {
      case 'critical':
        return 'border-l-4 border-l-rose-500 border-slate-800 bg-rose-950/20';
      case 'warning':
        return 'border-l-4 border-l-amber-500 border-slate-800 bg-amber-950/20';
      case 'success':
        return 'border-l-4 border-l-emerald-500 border-slate-800 bg-emerald-950/20';
      case 'info':
        return 'border-l-4 border-l-cyan-500 border-slate-800 bg-cyan-950/20';
      default:
        return 'border-l-4 border-l-slate-600 border-slate-800 bg-slate-900/40';
    }
  };

  return (
    <div
      role="article"
      aria-label={`${event.title} at ${event.timeDisplay}`}
      className={`p-3 rounded-lg border text-xs space-y-2 transition-all duration-200 ${getBorderColor()}`}
    >
      {/* Header Line: Actor, Time, Icon */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center space-x-2 min-w-0">
          {getIcon()}
          {event.actor ? (
            <div className="flex items-center space-x-1.5 truncate">
              {event.actor.flag && <span>{event.actor.flag}</span>}
              <span className="font-semibold text-slate-200 truncate">
                {event.actor.name}
              </span>
            </div>
          ) : (
            <span className="font-mono text-[10px] text-slate-400 uppercase">
              {event.eventType.replace(/_/g, ' ')}
            </span>
          )}
        </div>

        <span className="font-mono text-[11px] font-bold text-cyan-400 px-1.5 py-0.5 rounded bg-slate-950/80 border border-slate-800 shrink-0">
          {event.timeDisplay}
        </span>
      </div>

      {/* Title & Description */}
      <div>
        <h4 className="font-semibold text-slate-100 text-xs leading-snug">
          {event.title}
        </h4>
        <p className="text-[11px] text-slate-300 mt-1 leading-relaxed">
          {event.description}
        </p>
      </div>

      {/* RAG Grounding Citation Badge */}
      {event.ragCitation && (
        <div className="pt-1 flex items-center gap-1.5 text-[10px] font-mono text-cyan-300 bg-cyan-950/40 px-2 py-1 rounded border border-cyan-800/40">
          <BookOpen className="w-3 h-3 text-cyan-400 shrink-0" />
          <span className="truncate">RAG Grounded: {event.ragCitation}</span>
        </div>
      )}
    </div>
  );
};
