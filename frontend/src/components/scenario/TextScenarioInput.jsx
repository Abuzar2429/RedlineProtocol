import React, { useState } from 'react';
import { Sparkles, Send, AlertTriangle, RefreshCw, Cpu } from 'lucide-react';
import { apiClient } from '../../services/api/client';
import { useUIStore } from '../../stores/uiStore';

const SCENARIO_PRESETS = [
  {
    title: 'Automated Bio-Lab Synthesis Leak',
    severity: 'critical',
    origin: 'country_01',
    description: 'An advanced AI system at a sovereign research facility generates unverified pathogen synthesis sequences and begins transmitting them across international scientific networks.',
  },
  {
    title: 'Algorithmic Financial Market Flash Crash',
    severity: 'high',
    origin: 'country_03',
    description: 'Interconnected automated trading models trigger sudden, cascading sell-offs across international energy and debt markets, risking widespread economic instability.',
  },
  {
    title: 'Autonomous Border Drone Incursion',
    severity: 'high',
    origin: 'country_06',
    description: 'A fleet of autonomous border patrol drones malfunctions during a live exercise, drifting into foreign civilian airspace and ignoring standard recall signals.',
  },
  {
    title: 'Critical Satellite Network Disruption',
    severity: 'critical',
    origin: 'country_02',
    description: 'A rogue software update across a major commercial satellite constellation disrupts international GPS navigation and emergency communication channels.',
  },
];

export const TextScenarioInput = ({ onScenarioCreated, availableCountries = [] }) => {
  const { addToast } = useUIStore();

  const [isOpen, setIsOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [severity, setSeverity] = useState('high');
  const [originCountry, setOriginCountry] = useState(availableCountries[0]?.id || 'country_01');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleApplyPreset = (preset) => {
    setTitle(preset.title);
    setDescription(preset.description);
    setSeverity(preset.severity);
    setOriginCountry(preset.origin);
    setError(null);
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();

    if (!title.trim() || title.trim().length < 3) {
      setError('Title must be at least 3 characters.');
      return;
    }

    if (!description.trim() || description.trim().length < 10) {
      setError('Scenario description must be at least 10 characters.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const payload = {
        title: title.trim(),
        description: description.trim(),
        severity,
        origin_country: originCountry,
      };

      const created = await apiClient.createCustomScenario(payload);

      addToast({
        type: 'success',
        title: 'Scenario Created',
        message: `"${created.title}" is ready for testing.`,
      });

      // Reset form
      setTitle('');
      setDescription('');
      setIsOpen(false);

      if (onScenarioCreated) {
        onScenarioCreated(created);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to create scenario';
      setError(msg);
      addToast({
        type: 'error',
        title: 'Creation Failed',
        message: msg,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rounded-xl border border-cyan-500/40 bg-gradient-to-r from-cyan-950/20 via-slate-900 to-slate-950 p-4 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-cyan-950/80 border border-cyan-700/60 text-cyan-400">
            <Sparkles className="w-4 h-4 animate-pulse" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wide flex items-center gap-2">
              Create Custom Scenario
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-cyan-900/60 text-cyan-300 border border-cyan-700">
                DYNAMIC
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Describe any crisis scenario in plain language to simulate how nations respond.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
            isOpen
              ? 'bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700'
              : 'bg-gradient-to-r from-cyan-500 to-blue-600 text-slate-950 hover:from-cyan-400 hover:to-blue-500 shadow-md shadow-cyan-950/50'
          }`}
        >
          <Cpu className="w-3.5 h-3.5" />
          <span>{isOpen ? 'Close Input Panel' : '+ New Scenario'}</span>
        </button>
      </div>

      {isOpen && (
        <form onSubmit={handleSubmit} className="pt-3 border-t border-slate-800/80 space-y-4 animate-in fade-in duration-200">
          {/* Presets */}
          <div>
            <div className="text-[11px] font-mono uppercase text-slate-400 mb-1.5 flex items-center gap-1">
              <span>Sample Scenarios:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {SCENARIO_PRESETS.map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleApplyPreset(p)}
                  className="text-left text-[11px] font-mono px-2.5 py-1 rounded-md bg-slate-950/80 border border-slate-800 hover:border-cyan-500/60 text-slate-300 hover:text-cyan-300 transition-colors cursor-pointer"
                >
                  {p.title}
                </button>
              ))}
            </div>
          </div>

          {/* Form Fields */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="md:col-span-2">
              <label className="block text-xs font-mono text-slate-400 uppercase mb-1">
                Scenario Title *
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Rogue AI Agent Disrupts Regional Power Grid"
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 text-xs font-sans focus:outline-none focus:ring-1 focus:ring-cyan-500"
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-400 uppercase mb-1">
                Severity Level
              </label>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-cyan-500"
              >
                <option value="low">Low (Score: 0.35)</option>
                <option value="medium">Medium (Score: 0.60)</option>
                <option value="high">High (Score: 0.82)</option>
                <option value="critical">Critical (Score: 0.94)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-400 uppercase mb-1">
              Scenario Description *
            </label>
            <textarea
              required
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what happened, which systems or infrastructure are affected, and the international stakes involved..."
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 text-xs font-sans focus:outline-none focus:ring-1 focus:ring-cyan-500 leading-relaxed"
            />
          </div>

          {error && (
            <div className="p-2.5 rounded-lg bg-rose-950/50 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="px-3 py-1.5 rounded-lg border border-slate-700 text-slate-400 hover:text-slate-200 text-xs font-mono transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !title || !description}
              className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-mono font-semibold text-xs flex items-center gap-1.5 shadow-md shadow-cyan-950/40 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-all"
            >
              {isSubmitting ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Creating Scenario...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Add & Select Scenario</span>
                </>
              )}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default TextScenarioInput;
