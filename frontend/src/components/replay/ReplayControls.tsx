import React from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  SkipBack,
  SkipForward,
  FastForward,
  Sliders,
} from 'lucide-react';
import { useDemoStore } from '../../stores/demoStore';

interface ReplayControlsProps {
  className?: string;
  onSeekTick?: (tick: number) => void;
}

export const ReplayControls: React.FC<ReplayControlsProps> = ({
  className = '',
  onSeekTick,
}) => {
  const {
    activeReplay,
    replayTick,
    isPlayingReplay,
    playbackSpeed,
    visibleReplayEvents,
    playReplay,
    pauseReplay,
    stepReplay,
    seekReplayTick,
    setPlaybackSpeed,
  } = useDemoStore();

  if (!activeReplay) {
    return null;
  }

  const currentTick = replayTick;
  const maxTick = activeReplay.total_ticks;
  const currentEventCount = visibleReplayEvents.length;
  const totalEvents = activeReplay.total_events || activeReplay.events.length;

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const targetTick = parseInt(e.target.value, 10);
    seekReplayTick(targetTick);
    onSeekTick?.(targetTick);
  };

  const handleSpeedToggle = () => {
    const speeds = [0.5, 1, 2, 4];
    const currentIndex = speeds.indexOf(playbackSpeed);
    const nextSpeed = speeds[(currentIndex + 1) % speeds.length];
    setPlaybackSpeed(nextSpeed);
  };

  return (
    <div
      data-testid="replay-controls"
      className={`rounded-xl border border-purple-900/60 bg-slate-950/90 backdrop-blur p-4 shadow-lg shadow-purple-950/20 ${className}`}
    >
      {/* Header Info */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3 pb-2 border-b border-purple-950/50">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-purple-400" />
          <span className="text-xs font-mono font-semibold uppercase tracking-wider text-purple-300">
            Replay Playback Engine
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950 text-purple-200 border border-purple-800/80">
            {activeReplay.scenario_id}
          </span>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          <span className="text-slate-400">
            Tick:{' '}
            <strong className="text-purple-300 font-semibold">
              T+{String(currentTick).padStart(2, '0')}
            </strong>{' '}
            / T+{String(maxTick).padStart(2, '0')}
          </span>
          <span className="text-slate-500">|</span>
          <span className="text-slate-400">
            Events:{' '}
            <strong className="text-cyan-300 font-semibold">
              {currentEventCount}
            </strong>{' '}
            / {totalEvents}
          </span>
        </div>
      </div>

      {/* Progress / Seek Scrubber */}
      <div className="mb-4">
        <div className="relative flex items-center">
          <input
            type="range"
            min={0}
            max={Math.max(1, maxTick)}
            value={currentTick}
            onChange={handleSliderChange}
            data-testid="replay-scrubber"
            aria-label="Replay Timeline Scrubber"
            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-400"
          />
        </div>
        <div className="flex justify-between text-[10px] font-mono text-slate-500 mt-1">
          <span>T+00 (Genesis)</span>
          <span className="text-purple-400 font-medium">Authoritative Timeline Scrubber</span>
          <span>T+{String(maxTick).padStart(2, '0')} (Conclusion)</span>
        </div>
      </div>

      {/* Primary Playback Buttons */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          {/* Jump to start */}
          <button
            onClick={() => {
              seekReplayTick(0);
              onSeekTick?.(0);
            }}
            title="Restart to T+00"
            className="p-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          {/* Step Back */}
          <button
            onClick={() => {
              stepReplay(false);
              const newTick = useDemoStore.getState().replayTick;
              onSeekTick?.(newTick);
            }}
            disabled={currentTick <= 0}
            title="Step Back 1 Tick"
            className="p-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
          >
            <SkipBack className="w-3.5 h-3.5" />
          </button>

          {/* Play / Pause */}
          {isPlayingReplay ? (
            <button
              onClick={pauseReplay}
              data-testid="replay-pause-btn"
              title="Pause Playback"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-purple-600 bg-purple-700 hover:bg-purple-600 text-white text-xs font-semibold shadow-md transition-colors cursor-pointer"
            >
              <Pause className="w-3.5 h-3.5" />
              <span>Pause</span>
            </button>
          ) : (
            <button
              onClick={playReplay}
              data-testid="replay-play-btn"
              title="Play Replay"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-purple-500 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md transition-colors cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Play</span>
            </button>
          )}

          {/* Step Forward */}
          <button
            onClick={() => {
              stepReplay(true);
              const newTick = useDemoStore.getState().replayTick;
              onSeekTick?.(newTick);
            }}
            disabled={currentTick >= maxTick}
            title="Step Forward 1 Tick"
            className="p-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer"
          >
            <SkipForward className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Speed Selector */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleSpeedToggle}
            data-testid="replay-speed-btn"
            title="Toggle playback speed"
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg border border-slate-800 bg-slate-900/90 hover:bg-slate-800 text-xs font-mono font-medium text-slate-300 transition-colors cursor-pointer"
          >
            <FastForward className="w-3 h-3 text-purple-400" />
            <span>{playbackSpeed}x</span>
          </button>
        </div>
      </div>
    </div>
  );
};
