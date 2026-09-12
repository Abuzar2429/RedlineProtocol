import React from 'react';
import {
  AlertTriangle,
  FileCheck2,
  Vote,
  Shield,
  Clock,
  Sparkles,
  BookOpen,
} from 'lucide-react';
import type { FormattedEvent } from '../../utils/eventFormatter';

interface TimelineEventCardProps {
  event: FormattedEvent;
  isCurrent?: boolean;
}

const getCategoryBadge = (category: string) => {
  switch (category) {
    case 'crisis':
      return {
        icon: <AlertTriangle className="w-3 h-3 text-rose-400" />,
        label: 'CRISIS ANOMALY',
        border: 'border-rose-800/80 bg-rose-950/80 text-rose-300',
        dot: 'bg-rose-500 shadow-rose-500/50',
      };
    case 'negotiation':
      return {
        icon: <Vote className="w-3 h-3 text-cyan-400" />,
        label: 'NEGOTIATION',
        border: 'border-cyan-800/80 bg-cyan-950/80 text-cyan-300',
        dot: 'bg-cyan-500 shadow-cyan-500/50',
      };
    case 'decision':
      return {
        icon: <Shield className="w-3 h-3 text-indigo-400" />,
        label: 'POLICY ACTION',
        border: 'border-indigo-800/80 bg-indigo-950/80 text-indigo-300',
        dot: 'bg-indigo-500 shadow-indigo-500/50',
      };
    case 'system':
      return {
        icon: <Clock className="w-3 h-3 text-emerald-400" />,
        label: 'ENGINE MILESTONE',
        border: 'border-emerald-800/80 bg-emerald-950/80 text-emerald-300',
        dot: 'bg-emerald-500 shadow-emerald-500/50',
      };
    default:
      return {
        icon: <FileCheck2 className="w-3 h-3 text-slate-400" />,
        label: 'EVENT',
        border: 'border-slate-800 bg-slate-900 text-slate-400',
        dot: 'bg-slate-500',
      };
  }
};

export const TimelineEventCard: React.FC<TimelineEventCardProps> = ({ event, isCurrent }) => {
  const catStyle = getCategoryBadge(event.category);

  return (
    <div
      data-testid={`timeline-event-${event.id}`}
      className={`relative flex flex-col p-3 rounded-xl border transition-all duration-200 text-left ${
        isCurrent
          ? 'bg-slate-900 border-cyan-500/70 shadow-lg shadow-cyan-950/30'
          : 'bg-slate-950/70 border-slate-800/90 hover:border-slate-700/80 hover:bg-slate-900/60'
      }`}
    >
      {/* Current Tick indicator banner */}
      {isCurrent && (
        <div className="absolute -top-2.5 right-3 px-2 py-0.5 rounded-full bg-cyan-500 text-slate-950 font-mono text-[9px] font-bold tracking-wider uppercase shadow-md flex items-center space-x-1">
          <Sparkles className="w-2.5 h-2.5" />
          <span>CURRENT TICK</span>
        </div>
      )}

      {/* Header: Tick + Category + Actor */}
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <div className="flex items-center space-x-2">
          {/* Tick Badge */}
          <span className="font-mono text-xs font-bold text-cyan-300 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
            T+{String(event.tick).padStart(2, '0')}
          </span>

          {/* Category Tag */}
          <span
            className={`inline-flex items-center space-x-1 text-[10px] font-mono font-semibold px-2 py-0.5 rounded-md border ${catStyle.border}`}
          >
            {catStyle.icon}
            <span>{catStyle.label}</span>
          </span>
        </div>

        {/* Actor Pill */}
        {event.actor && (
          <div className="flex items-center space-x-1 text-[11px] font-mono text-slate-300 bg-slate-900/80 px-2 py-0.5 rounded border border-slate-800">
            <span>{event.actor.flag || '🌐'}</span>
            <span className="truncate max-w-[120px]">{event.actor.name}</span>
          </div>
        )}
      </div>

      {/* Title */}
      <h4 className="text-xs font-bold text-slate-200 mb-1 leading-snug">
        {event.title}
      </h4>

      {/* Description */}
      <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed mb-1.5">
        {event.description}
      </p>

      {/* Footer Citations */}
      {event.ragCitation && (
        <div className="mt-auto pt-1.5 border-t border-slate-800/60 flex items-center space-x-1 text-[10px] font-mono text-cyan-400">
          <BookOpen className="w-3 h-3" />
          <span className="truncate">Source: {event.ragCitation}</span>
        </div>
      )}
    </div>
  );
};
