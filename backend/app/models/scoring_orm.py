"""
SQLAlchemy ORM models for Phase 7 Deterministic Scoring Engine.

Maps scoring results, individual metric evaluations, and immutable input snapshots.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ScoringResultORM(Base):
    """
    Persisted evaluation record for a simulation outcome.
    """
    __tablename__ = "scoring_results"

    scoring_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    simulation_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    scenario_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    simulation_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    formula_version: Mapped[str] = mapped_column(String(16), default="1.0", nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    score_grade: Mapped[str] = mapped_column(String(4), nullable=False)
    performance_headline: Mapped[str] = mapped_column(Text, nullable=False)
    simulation_status: Mapped[str] = mapped_column(String(32), nullable=False)
    calculated_at_tick: Mapped[int] = mapped_column(Integer, nullable=False)
    is_authoritative: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mode_comparison_ready: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to metric breakdowns
    metric_breakdowns: Mapped[List["MetricResultORM"]] = relationship(
        "MetricResultORM",
        back_populates="scoring_result",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    # Optional foreign key / link to snapshot
    snapshot_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("scoring_snapshots.snapshot_id", ondelete="SET NULL"), nullable=True
    )
    snapshot: Mapped[Optional["ScoringSnapshotORM"]] = relationship(
        "ScoringSnapshotORM", back_populates="scoring_results"
    )


class MetricResultORM(Base):
    """
    Persisted breakdown for one of the four deterministic metrics.
    """
    __tablename__ = "metric_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scoring_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("scoring_results.scoring_id", ondelete="CASCADE"), index=True, nullable=False
    )
    metric_id: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    display_value: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_score: Mapped[float] = mapped_column(Float, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    weighted_score: Mapped[float] = mapped_column(Float, nullable=False)
    interpretation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    scoring_result: Mapped["ScoringResultORM"] = relationship(
        "ScoringResultORM", back_populates="metric_breakdowns"
    )


class ScoringSnapshotORM(Base):
    """
    Persisted immutable input snapshot for audit and replay validation.
    """
    __tablename__ = "scoring_snapshots"

    snapshot_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    simulation_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    scenario_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    final_tick: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    scoring_results: Mapped[List["ScoringResultORM"]] = relationship(
        "ScoringResultORM", back_populates="snapshot"
    )
