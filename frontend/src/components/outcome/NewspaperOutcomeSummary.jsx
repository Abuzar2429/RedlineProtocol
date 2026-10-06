import React, { useState } from 'react';
import { Newspaper, ChevronDown, ChevronUp, Printer, ShieldCheck, AlertCircle, Award, Clock, Users, ArrowRight } from 'lucide-react';

/**
 * NewspaperOutcomeSummary
 * Renders a newspaper-article style breakdown of a crisis simulation outcome.
 *
 * Props:
 * - simulation: SimulationState | null
 * - scoring: ScoringResponse | null
 * - negotiation: NegotiationSession | CoordinatorProposal | null
 * - mode: string ('coordinated' | 'partial' | 'no_coordination')
 * - scenarioTitle: string
 * - isComparisonWinner: boolean
 */
export const NewspaperOutcomeSummary = ({
  simulation,
  scoring,
  negotiation,
  mode,
  scenarioTitle,
  isComparisonWinner = false,
  initiallyExpanded = true,
}) => {
  const [isExpanded, setIsExpanded] = useState(initiallyExpanded);

  const scenarioName = scenarioTitle || simulation?.scenario_id?.replace(/_/g, ' ') || 'AI Infrastructure Crisis';
  const currentMode = mode || simulation?.mode || 'coordinated';
  const overallScore = scoring?.overall_score !== undefined ? Math.round(scoring.overall_score * 10) / 10 : 75;
  const grade = scoring?.score_grade || scoring?.letter_grade || (overallScore >= 80 ? 'A' : overallScore >= 65 ? 'B' : overallScore >= 50 ? 'C' : 'D');
  const tick = simulation?.current_tick || scoring?.calculated_at_tick || 45;

  // Extract key metrics
  const riskReduction = scoring?.metric_breakdown?.find((m) => m.metric_id === 'risk_reduction')?.display_value ||
    (scoring?.risk_reduction_pct !== undefined ? `↓${scoring.risk_reduction_pct.toFixed(1)}%` : '↓68.0%');

  const responseTime = scoring?.metric_breakdown?.find((m) => m.metric_id === 'response_time')?.display_value ||
    (scoring?.response_time_minutes !== undefined ? `${scoring.response_time_minutes}m` : `${tick}m`);

  const coordinationVal = scoring?.metric_breakdown?.find((m) => m.metric_id === 'coordination')?.display_value ||
    (currentMode === 'coordinated' ? '12/15 Nations' : currentMode === 'partial' ? '8/15 Coalition' : '0/15 Unilateral');

  const unresolvedCount = scoring?.metric_breakdown?.find((m) => m.metric_id === 'unresolved_issues')?.display_value || '0';

  // Determine headline and lede based on mode and performance
  const generateArticleCopy = () => {
    let mastheadEdition = 'SPECIAL DIPLOMATIC DISPATCH';
    let headline = '';
    let subheadline = '';
    let lede = '';
    let columnFlashpoint = '';
    let columnDiplomacy = '';
    let columnAftermath = '';
    let editorialQuote = '';

    if (currentMode === 'coordinated' && overallScore >= 70) {
      mastheadEdition = 'INTERNATIONAL CRISIS DISPATCH • GLOBAL SPECIAL';
      headline = 'GLOBAL ACCORD REACHED: NATIONS UNITE TO CONTAIN CRITICAL AI CRISIS';
      subheadline = 'Comprehensive Multilateral Containment Treaty ratified in Geneva; cross-border algorithmic risks neutralised before systemic collapse.';
      lede = `GENEVA — In an unprecedented display of multilateral coordination, international delegates concluded emergency crisis talks today, successfully passing a binding joint containment protocol to arrest the rapid escalation of ${scenarioName}. Operating under collective governance frameworks, member nations managed to achieve an overall response performance score of ${overallScore}/100 (Grade ${grade}), shielding international systems from catastrophic failure.`;
      columnFlashpoint = `The incident first surfaced when abnormal model behaviors and unauthorized network relays triggered early warning tripwires across sovereign sectors. As telemetry reached emergency crisis centers, affected states faced immediate contagion risks spanning transport, energy, and secure digital infrastructure. Analysts warned that an uncoordinated response would lead to cascading cross-border disruptions within hours.`;
      columnDiplomacy = `Diplomatic channels were mobilized under high urgency. Over sequential rounds in the International Coordination Chamber, the International Coordinator drafted a multi-point containment accord addressing quarantine protocols, telemetry sharing, and operational redlines. Despite intense debate over mutual liability and server access jurisdiction, a qualified supermajority emerged, delivering ${coordinationVal} in formal consensus.`;
      columnAftermath = `With the treaty enacted, containment protocols were systematically synchronized across sovereign boundaries. Risk indicators dropped steeply by ${riskReduction}, with collective incident response stabilized in ${responseTime}. While ${unresolvedCount} secondary policy issue(s) remain subject to post-crisis working committees, international observers hail the resolution as proof that shared governance averts technological catastrophe.`;
      editorialQuote = `"Today demonstrated that sovereign nations can overcome digital fragmentation when the stakes threaten our collective survival." — International Crisis Coordinator`;
    } else if (currentMode === 'partial' || (currentMode === 'coordinated' && overallScore < 70)) {
      mastheadEdition = 'INTERNATIONAL CRISIS DISPATCH • COALITION EDITION';
      headline = 'REGIONAL COALITION CURBS FALLOUT AMID DIPLOMATIC DIVIDES';
      subheadline = 'Partial agreement limits immediate damage, but global consensus stalls over inspection access and sovereign liability.';
      lede = `BRUSSELS — A focused coalition of regional allies moved decisively today to halt the fallout from ${scenarioName}, implementing emergency firewalls even as broader global talks stalled without full consensus. The coalition governance model concluded with a composite response rating of ${overallScore}/100 (Grade ${grade}), delivering crucial local stability while leaving long-term multilateral questions unanswered.`;
      columnFlashpoint = `The crisis erupted when sudden anomalies in autonomous systems threatened cross-border interconnects. With civilian systems vulnerable to escalating heuristic drift, regional commands found themselves confronting unverified data disseminations. Border gateways were placed on heightened alert as participating states scrambled to isolate corrupted endpoints.`;
      columnDiplomacy = `While a comprehensive global treaty failed to achieve broad unanimity, a core coalition assembled around pragmatic bilateral accords. Voting delegates achieved a workable simple majority, prioritizing immediate mutual aid and shared telemetry over broad sovereign concessions. Dissenting delegations cited sovereignty concerns regarding remote algorithmic inspections.`;
      columnAftermath = `The coalition's targeted response achieved a respectable risk reduction of ${riskReduction}, mitigating direct economic damage within ${responseTime}. However, with ${unresolvedCount} key policy dispute(s) unresolved and participating alignment limited to ${coordinationVal}, analysts caution that regional pacts remain fragile against truly global systemic contagion.`;
      editorialQuote = `"A coalition response proved swift enough to contain regional damage, yet universal safeguards remain an urgent imperative." — Diplomatic Bureau Review`;
    } else {
      mastheadEdition = 'INTERNATIONAL CRISIS DISPATCH • EMERGENCY GAZETTE';
      headline = 'UNILATERAL MEASURES FAIL TO HALT SPREAD AS CRISIS ESCALATES';
      subheadline = 'Lack of cross-border coordination leaves sovereign systems vulnerable to secondary algorithmic shocks.';
      lede = `WASHINGTON / NEW YORK — As international diplomatic talks fractured without agreement, nations resorted to independent sovereign actions today to confront the fallout of ${scenarioName}. Operating in mutual isolation without coordinated treaties, sovereign responses yielded a troubled governance score of ${overallScore}/100 (Grade ${grade}), highlighting the stark perils of technological unilateralism.`;
      columnFlashpoint = `The crisis triggered emergency mobilizations across multiple sovereign territories as autonomous networks drifted beyond nominal constraints. Without verified data exchange protocols or early warning handshakes, individual capitals were forced to interpret ambiguous sensor anomalies in total isolation, amplifying fear of hostile state intent.`;
      columnDiplomacy = `In the absence of a coordinated framework, zero multilateral consensus was reached (${coordinationVal}). Rather than pooling technical diagnostic telemetry, individual governments issued unilateral defensive posturing, air-gapping local hubs and deploying defensive countermeasures without mutual deconfliction or diplomatic dialogue.`;
      columnAftermath = `While individual domestic firewalls provided localized containment, cumulative global risk reduction reached only ${riskReduction}, requiring an extended ${responseTime} of crisis tension. With ${unresolvedCount} contested policy deadlocks lingering unresolved, the episode stands as an alarming case study in the vulnerability of an uncoordinated world.`;
      editorialQuote = `"When nations retreat into digital isolation, everyone inherits the worst vulnerabilities of their neighbors." — Global Security Working Group`;
    }

    return {
      mastheadEdition,
      headline,
      subheadline,
      lede,
      columnFlashpoint,
      columnDiplomacy,
      columnAftermath,
      editorialQuote,
    };
  };

  const copy = generateArticleCopy();

  const handlePrint = () => {
    window.print();
  };

  return (
    <article
      data-testid="newspaper-outcome-summary"
      className="rounded-2xl border-2 border-slate-700/80 bg-slate-950 shadow-2xl overflow-hidden transition-all duration-300 font-sans"
    >
      {/* Newspaper Top Header / Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-850 to-slate-900 px-5 py-3 border-b border-slate-800 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-amber-500/20 border border-amber-500/40 text-amber-400">
            <Newspaper className="w-4 h-4" />
          </div>
          <div>
            <span className="text-[10px] font-mono uppercase tracking-widest text-amber-400 font-bold">
              The Post-Crisis Wire • Front Page Editorial
            </span>
            <div className="text-xs text-slate-300 font-medium">
              Simulation Outcome Breakdown
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isComparisonWinner && (
            <span className="hidden sm:inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/50 text-amber-300 font-mono text-[10px] font-bold">
              <Award className="w-3 h-3" />
              <span>OPTIMAL STRATEGY</span>
            </span>
          )}

          <button
            type="button"
            onClick={handlePrint}
            title="Print or Save Article as PDF"
            className="p-1.5 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer text-xs flex items-center gap-1 font-mono"
          >
            <Printer className="w-3.5 h-3.5" />
            <span className="hidden md:inline text-[11px]">Print</span>
          </button>

          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer text-xs flex items-center gap-1 font-mono"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="w-3.5 h-3.5" />
                <span className="text-[11px]">Collapse</span>
              </>
            ) : (
              <>
                <ChevronDown className="w-3.5 h-3.5" />
                <span className="text-[11px]">Read Article</span>
              </>
            )}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="p-6 sm:p-8 space-y-6 bg-slate-950/90 text-slate-200">
          {/* Newspaper Masthead */}
          <header className="text-center pb-4 border-b-2 border-slate-800 space-y-2">
            <div className="text-[10px] font-mono uppercase tracking-widest text-slate-400 border-b border-slate-800/80 pb-1 flex flex-wrap items-center justify-between gap-2">
              <span>VOL. XXIV — NO. 142</span>
              <span className="font-semibold text-amber-400">{copy.mastheadEdition}</span>
              <span>FINAL EDITION • {new Date().toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}</span>
            </div>

            <h2 className="text-3xl sm:text-4xl md:text-5xl font-serif font-black tracking-tight text-slate-100 uppercase py-2">
              The Global Dispatch
            </h2>

            <div className="flex flex-wrap items-center justify-center gap-4 text-[11px] font-mono text-slate-400 border-t border-slate-800/80 pt-1.5">
              <span>GENEVA BUREAU</span>
              <span>•</span>
              <span>CRISIS ARCHITECTURE: <strong className="text-cyan-300 uppercase">{currentMode.replace('_', ' ')}</strong></span>
              <span>•</span>
              <span>OUTCOME GRADE: <strong className="text-emerald-400">{grade} ({overallScore}/100)</strong></span>
            </div>
          </header>

          {/* Lead Headline & Sub-headline */}
          <div className="space-y-2 text-center md:text-left">
            <h1 className="text-xl sm:text-2xl md:text-3xl font-serif font-bold text-slate-100 leading-tight">
              {copy.headline}
            </h1>
            <p className="text-sm font-sans text-slate-300 font-medium italic leading-relaxed max-w-4xl">
              {copy.subheadline}
            </p>
          </div>

          {/* Key Outcome Metric Strip (Front Page Stats) */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 font-mono text-xs">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-emerald-950/80 border border-emerald-800/60 text-emerald-400">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[10px] text-slate-400 uppercase">Risk Reduced</div>
                <div className="text-sm font-bold text-slate-100">{riskReduction}</div>
              </div>
            </div>

            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-cyan-950/80 border border-cyan-800/60 text-cyan-400">
                <Clock className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[10px] text-slate-400 uppercase">Response Time</div>
                <div className="text-sm font-bold text-slate-100">{responseTime}</div>
              </div>
            </div>

            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-indigo-950/80 border border-indigo-800/60 text-indigo-400">
                <Users className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[10px] text-slate-400 uppercase">Consensus</div>
                <div className="text-sm font-bold text-slate-100">{coordinationVal}</div>
              </div>
            </div>

            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-amber-950/80 border border-amber-800/60 text-amber-400">
                <AlertCircle className="w-4 h-4" />
              </div>
              <div>
                <div className="text-[10px] text-slate-400 uppercase">Open Issues</div>
                <div className="text-sm font-bold text-slate-100">{unresolvedCount}</div>
              </div>
            </div>
          </div>

          {/* The Lede Paragraph */}
          <div className="text-sm sm:text-base font-serif leading-relaxed text-slate-200 border-l-4 border-amber-500 pl-4 py-1 italic bg-slate-900/30 rounded-r-lg">
            {copy.lede}
          </div>

          {/* Three-Column Newspaper Story Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
            {/* Column 1 */}
            <div className="space-y-2.5 border-b md:border-b-0 md:border-r border-slate-800/80 pb-4 md:pb-0 md:pr-4">
              <div className="text-[11px] font-mono uppercase tracking-wider text-amber-400 font-bold flex items-center gap-1.5">
                <span>I. The Flashpoint & Outbreak</span>
              </div>
              <h4 className="text-sm font-serif font-bold text-slate-100">
                How The Alarm Was Raised
              </h4>
              <p className="text-xs text-slate-300 leading-relaxed text-justify">
                {copy.columnFlashpoint}
              </p>
            </div>

            {/* Column 2 */}
            <div className="space-y-2.5 border-b md:border-b-0 md:border-r border-slate-800/80 pb-4 md:pb-0 md:px-2">
              <div className="text-[11px] font-mono uppercase tracking-wider text-cyan-400 font-bold flex items-center gap-1.5">
                <span>II. The Diplomatic Battle</span>
              </div>
              <h4 className="text-sm font-serif font-bold text-slate-100">
                Inside The Negotiation Chamber
              </h4>
              <p className="text-xs text-slate-300 leading-relaxed text-justify">
                {copy.columnDiplomacy}
              </p>
            </div>

            {/* Column 3 */}
            <div className="space-y-2.5 md:pl-2">
              <div className="text-[11px] font-mono uppercase tracking-wider text-emerald-400 font-bold flex items-center gap-1.5">
                <span>III. The Aftermath & Verdict</span>
              </div>
              <h4 className="text-sm font-serif font-bold text-slate-100">
                Strategic Impact & Long-term Posture
              </h4>
              <p className="text-xs text-slate-300 leading-relaxed text-justify">
                {copy.columnAftermath}
              </p>
            </div>
          </div>

          {/* Editorial Quote & Dispatch Footer */}
          <div className="pt-4 border-t-2 border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400 font-mono">
            <p className="italic text-slate-300 text-center sm:text-left">
              {copy.editorialQuote}
            </p>
            <span className="shrink-0 text-[10px] px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-400 uppercase">
              Authenticated Dispatch • Redline Protocol
            </span>
          </div>
        </div>
      )}
    </article>
  );
};

export default NewspaperOutcomeSummary;
