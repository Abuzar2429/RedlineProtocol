import React, { useState } from 'react';
import {
  FileText,
  Vote as VoteIcon,
  CheckCircle,
  XCircle,
  Clock,
  BookOpen,
  Check,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { useSimulationStore } from '../../stores/simulationStore';
import { COUNTRY_GEO_REGISTRY } from '../../utils/geoCoordinates';
import type {
  CoordinatorProposal,
  NegotiationSession,
  NegotiationRound,
  VotingResult,
  ProposalVersion,
} from '../../types';

export const NegotiationPanel: React.FC = () => {
  const proposals = useSimulationStore((s) => s.proposals);
  const negotiationSessions = useSimulationStore((s) => s.negotiationSessions);
  const negotiationsRaw = useSimulationStore((s) => s.negotiations);

  // Active negotiation session if available
  const latestSession: NegotiationSession | undefined =
    negotiationSessions.length > 0
      ? negotiationSessions[negotiationSessions.length - 1]
      : (negotiationsRaw[negotiationsRaw.length - 1] as unknown as NegotiationSession | undefined);

  // Active coordinator proposal
  const latestProposal: CoordinatorProposal | undefined =
    proposals.length > 0 ? proposals[0] : undefined;

  // Selected round tab if history is present
  const rounds: NegotiationRound[] = latestSession?.rounds ?? [];
  const [selectedRoundIndex, setSelectedRoundIndex] = useState<number>(
    rounds.length > 0 ? rounds.length - 1 : 0
  );

  // Synchronize tab when new rounds arrive
  const activeRound: NegotiationRound | undefined =
    rounds.length > 0 ? rounds[Math.min(selectedRoundIndex, rounds.length - 1)] : undefined;

  // Selected or active proposal version
  const activeProposalVersion: ProposalVersion | CoordinatorProposal | undefined =
    activeRound?.proposal_version || latestProposal;

  // Voting result for active round or session outcome
  const votingResult: VotingResult | undefined =
    activeRound?.voting_result || latestSession?.outcome?.final_vote_result || undefined;

  // If no proposal and no negotiation session has started
  if (!latestProposal && !latestSession) {
    return (
      <div
        data-testid="negotiation-panel-empty"
        className="h-full rounded-2xl border border-slate-800 bg-slate-900/80 backdrop-blur-md p-5 flex flex-col items-center justify-center text-center shadow-lg min-h-[420px]"
      >
        <div className="p-3.5 rounded-2xl bg-slate-800/80 border border-slate-700/60 text-slate-400 mb-3 shadow-inner">
          <VoteIcon className="w-8 h-8 text-cyan-400/80" />
        </div>
        <div className="text-[11px] font-mono text-cyan-400 uppercase tracking-wider mb-1.5 font-semibold">
          International Coordination Chamber
        </div>
        <h3 className="text-sm font-bold text-slate-200 mb-2">
          No Negotiation Session Active
        </h3>
        <p className="text-xs text-slate-400 max-w-sm leading-relaxed mb-4">
          The International Coordinator will table a multilateral treaty proposal once crisis detection and national positions are established.
        </p>
        <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] font-mono text-slate-400">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span>Standing by for Coordinator Treaty Draft</span>
        </div>
      </div>
    );
  }

  // Determine status display
  const sessionStatus = latestSession?.status || latestProposal?.status || 'PROPOSED';
  const currentRoundNum = activeRound?.round_number || latestSession?.current_round || latestProposal?.round || 1;
  const maxRounds = latestSession?.max_rounds || 3;

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'ACCEPTED':
      case 'PASSED':
        return (
          <span className="px-2.5 py-1 rounded-md bg-emerald-950/80 border border-emerald-700 text-emerald-300 font-mono text-xs font-bold flex items-center space-x-1.5">
            <CheckCircle className="w-3.5 h-3.5" />
            <span>ACCEPTED</span>
          </span>
        );
      case 'FAILED':
      case 'BREAKDOWN':
        return (
          <span className="px-2.5 py-1 rounded-md bg-rose-950/80 border border-rose-700 text-rose-300 font-mono text-xs font-bold flex items-center space-x-1.5">
            <XCircle className="w-3.5 h-3.5" />
            <span>FAILED</span>
          </span>
        );
      case 'REVISION_REQUIRED':
      case 'REVISION_REQUESTED':
        return (
          <span className="px-2.5 py-1 rounded-md bg-amber-950/80 border border-amber-700 text-amber-300 font-mono text-xs font-bold flex items-center space-x-1.5">
            <Clock className="w-3.5 h-3.5" />
            <span>REVISION REQUIRED</span>
          </span>
        );
      case 'NO_QUORUM':
        return (
          <span className="px-2.5 py-1 rounded-md bg-rose-950/80 border border-rose-700 text-rose-300 font-mono text-xs font-bold flex items-center space-x-1.5">
            <XCircle className="w-3.5 h-3.5" />
            <span>NO QUORUM</span>
          </span>
        );
      case 'VOTING':
        return (
          <span className="px-2.5 py-1 rounded-md bg-cyan-950/80 border border-cyan-700 text-cyan-300 font-mono text-xs font-bold flex items-center space-x-1.5 animate-pulse">
            <VoteIcon className="w-3.5 h-3.5" />
            <span>VOTING IN PROGRESS</span>
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 rounded-md bg-indigo-950/80 border border-indigo-700 text-indigo-300 font-mono text-xs font-bold flex items-center space-x-1.5">
            <FileText className="w-3.5 h-3.5" />
            <span>{status.replace(/_/g, ' ')}</span>
          </span>
        );
    }
  };

  // Extract supporting & opposing countries
  const supportingCountries: string[] =
    votingResult?.approving_countries ||
    latestSession?.outcome?.supporting_countries ||
    latestProposal?.supporting_countries ||
    [];

  const opposingCountries: string[] =
    votingResult?.opposing_countries ||
    latestSession?.outcome?.opposing_countries ||
    latestProposal?.opposing_countries ||
    [];

  const abstainingCountries: string[] =
    votingResult?.abstaining_countries ||
    latestSession?.outcome?.abstaining_countries ||
    [];

  // Render country chip helper
  const renderCountryPill = (countryId: string) => {
    const info = COUNTRY_GEO_REGISTRY[countryId];
    return (
      <span
        key={countryId}
        className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-800/90 border border-slate-700 text-[11px] font-mono text-slate-200"
      >
        <span>{info?.flag || '🌐'}</span>
        <span>{info?.name || countryId}</span>
      </span>
    );
  };

  return (
    <div
      data-testid="negotiation-panel"
      className="h-full rounded-2xl border border-slate-800 bg-slate-900/80 backdrop-blur-md p-4 flex flex-col shadow-lg space-y-4"
    >
      {/* Panel Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-slate-800 gap-2">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-xl bg-slate-800/80 border border-slate-700/60 text-cyan-400">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xs font-bold text-slate-100 uppercase tracking-wider font-mono">
                Multilateral Negotiation Chamber
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-cyan-300 border border-slate-700">
                Round {currentRoundNum} of {maxRounds}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono mt-0.5">
              Phase 5–6 International Coordinator Treaty Engine
            </p>
          </div>
        </div>

        <div>{getStatusBadge(sessionStatus)}</div>
      </div>

      {/* Round Tabs (if multiple rounds executed) */}
      {rounds.length > 1 && (
        <div className="flex items-center space-x-1 p-1 rounded-xl bg-slate-950/60 border border-slate-800">
          {rounds.map((r, idx) => (
            <button
              key={r.round_number}
              onClick={() => setSelectedRoundIndex(idx)}
              className={`flex-1 px-3 py-1 text-xs font-mono rounded-lg transition-colors cursor-pointer ${
                selectedRoundIndex === idx
                  ? 'bg-slate-800 text-cyan-300 font-bold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Round {r.round_number}
            </button>
          ))}
        </div>
      )}

      {/* Main Proposal Card */}
      {activeProposalVersion && (
        <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800/90 space-y-3">
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="flex items-center space-x-2 mb-1">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-cyan-400 bg-cyan-950/80 border border-cyan-800/80 px-2 py-0.5 rounded">
                  {'version' in activeProposalVersion
                    ? `Proposal v${activeProposalVersion.version}`
                    : 'Joint Response Treaty'}
                </span>
                <span className="text-xs text-slate-400 font-mono">
                  {latestProposal?.proposal_type || 'JOINT_RESPONSE'}
                </span>
              </div>
              <h3 className="text-sm font-bold text-slate-100 tracking-wide">
                {activeProposalVersion.title}
              </h3>
            </div>

            {latestProposal?.confidence !== undefined && (
              <div
                className="px-2 py-1 rounded bg-slate-900 border border-slate-800 text-[10px] font-mono text-slate-300 text-right"
                title="Coordinator treaty confidence score"
              >
                <div className="text-[9px] text-slate-500 uppercase">Confidence</div>
                <div className="font-bold text-cyan-300">
                  {Math.round(latestProposal.confidence * 100)}%
                </div>
              </div>
            )}
          </div>

          {/* Proposal Summary */}
          <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-3 rounded-lg border border-slate-800/60">
            {activeProposalVersion.summary}
          </p>

          {/* Actionable Treaty Items */}
          {activeProposalVersion.items && activeProposalVersion.items.length > 0 && (
            <div className="space-y-1.5">
              <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold flex items-center space-x-1.5">
                <Sparkles className="w-3 h-3 text-cyan-400" />
                <span>Proposed Actionable Provisions</span>
              </div>
              <ul className="space-y-1">
                {activeProposalVersion.items.map((item, idx) => (
                  <li
                    key={idx}
                    className="text-xs text-slate-300 flex items-start space-x-2 bg-slate-900/40 p-2 rounded border border-slate-800/40"
                  >
                    <span className="font-mono text-cyan-400 font-bold text-[11px] select-none">
                      §{idx + 1}
                    </span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Public Multilateral Rationale */}
          {activeProposalVersion.rationale && (
            <div className="pt-2 border-t border-slate-800/60">
              <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 mb-1">
                Public Collective Rationale
              </div>
              <p className="text-[11px] text-slate-400 italic">
                "{activeProposalVersion.rationale}"
              </p>
            </div>
          )}

          {/* Governance Framework Citations (Phase 9) */}
          {latestProposal?.rag_sources && latestProposal.rag_sources.length > 0 && (
            <div className="pt-2 border-t border-slate-800/60 flex items-center space-x-2 text-[10px] font-mono text-slate-400">
              <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
              <span>Grounded in: {latestProposal.rag_sources.join(', ')}</span>
            </div>
          )}
        </div>
      )}

      {/* Country Alignment Breakdown */}
      <div className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800/90 space-y-2.5">
        <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
          Country Alignment Positions
        </div>

        <div className="space-y-2">
          {/* Supporting */}
          <div>
            <div className="flex items-center space-x-1.5 text-xs text-emerald-400 font-semibold mb-1">
              <Check className="w-3.5 h-3.5" />
              <span>Endorsing ({supportingCountries.length})</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {supportingCountries.length > 0 ? (
                supportingCountries.map(renderCountryPill)
              ) : (
                <span className="text-xs text-slate-500 italic">No formal approvals recorded</span>
              )}
            </div>
          </div>

          {/* Opposing */}
          {opposingCountries.length > 0 && (
            <div className="pt-1.5 border-t border-slate-800/60">
              <div className="flex items-center space-x-1.5 text-xs text-rose-400 font-semibold mb-1">
                <XCircle className="w-3.5 h-3.5" />
                <span>Dissenting ({opposingCountries.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {opposingCountries.map(renderCountryPill)}
              </div>
            </div>
          )}

          {/* Abstaining / Undecided */}
          {abstainingCountries.length > 0 && (
            <div className="pt-1.5 border-t border-slate-800/60">
              <div className="flex items-center space-x-1.5 text-xs text-amber-400 font-semibold mb-1">
                <Clock className="w-3.5 h-3.5" />
                <span>Abstaining / Deliberating ({abstainingCountries.length})</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {abstainingCountries.map(renderCountryPill)}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Voting Telemetry & Quorum Section */}
      {votingResult && (
        <div
          data-testid="negotiation-voting-result"
          className="p-3.5 rounded-xl bg-slate-950/50 border border-slate-800/90 space-y-3"
        >
          <div className="flex items-center justify-between">
            <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold flex items-center space-x-1.5">
              <VoteIcon className="w-3.5 h-3.5 text-cyan-400" />
              <span>Deterministic Voting Outcome</span>
            </div>
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                votingResult.passed
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
              }`}
            >
              {votingResult.status}
            </span>
          </div>

          {/* Vote Counts */}
          <div className="grid grid-cols-3 gap-2 text-center font-mono">
            <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
              <div className="text-[10px] text-emerald-400">APPROVE</div>
              <div className="text-lg font-bold text-slate-100">{votingResult.votes_for}</div>
            </div>
            <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
              <div className="text-[10px] text-rose-400">REJECT</div>
              <div className="text-lg font-bold text-slate-100">{votingResult.votes_against}</div>
            </div>
            <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
              <div className="text-[10px] text-amber-400">UNDECIDED</div>
              <div className="text-lg font-bold text-slate-100">{votingResult.abstentions}</div>
            </div>
          </div>

          {/* Quorum & Threshold Progress */}
          <div className="space-y-2 pt-1">
            {/* Quorum Meter */}
            <div>
              <div className="flex justify-between text-[11px] font-mono text-slate-400 mb-1">
                <span>Quorum Participation: {Math.round(votingResult.participation_rate * 100)}%</span>
                <span className={votingResult.is_quorum_met ? 'text-emerald-400 font-bold' : 'text-rose-400'}>
                  {votingResult.is_quorum_met ? 'Quorum Met' : 'Quorum Not Met'}
                </span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    votingResult.is_quorum_met ? 'bg-emerald-500' : 'bg-rose-500'
                  }`}
                  style={{ width: `${Math.min(100, Math.round(votingResult.participation_rate * 100))}%` }}
                />
              </div>
            </div>

            {/* Threshold Meter */}
            <div>
              <div className="flex justify-between text-[11px] font-mono text-slate-400 mb-1">
                <span>
                  Approval Threshold: {Math.round(votingResult.achieved_threshold * 100)}% / {Math.round(votingResult.required_threshold * 100)}%
                </span>
                <span className={votingResult.passed ? 'text-emerald-400 font-bold' : 'text-slate-400'}>
                  {votingResult.passed ? 'Threshold Achieved' : 'Insufficient'}
                </span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    votingResult.passed ? 'bg-emerald-500' : 'bg-amber-500'
                  }`}
                  style={{ width: `${Math.min(100, Math.round(votingResult.achieved_threshold * 100))}%` }}
                />
              </div>
            </div>
          </div>

          {votingResult.failure_reason && (
            <p className="text-[11px] text-rose-400 font-mono mt-1">
              Note: {votingResult.failure_reason}
            </p>
          )}
        </div>
      )}

      {/* Unresolved Issues List (if any) */}
      {(() => {
        const issues: string[] =
          (activeRound?.unresolved_issues && activeRound.unresolved_issues.length > 0
            ? activeRound.unresolved_issues
            : latestSession?.outcome?.unresolved_issues) ||
          latestProposal?.unresolved_issues ||
          [];
        if (issues.length === 0) return null;

        return (
          <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800/90 space-y-1.5">
            <div className="text-[10px] font-mono uppercase tracking-wider text-amber-400 font-semibold">
              Unresolved Policy Issues
            </div>
            <ul className="space-y-1">
              {issues.map((issue: string, idx: number) => (
                <li key={idx} className="text-xs text-slate-300 flex items-center space-x-1.5">
                  <ChevronRight className="w-3 h-3 text-amber-400 shrink-0" />
                  <span>{issue}</span>
                </li>
              ))}
            </ul>
          </div>
        );
      })()}
    </div>
  );
};
