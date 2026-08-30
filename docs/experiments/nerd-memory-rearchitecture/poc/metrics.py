from __future__ import annotations

from statistics import mean
from typing import Any, Mapping, Sequence

from .model import Advice, Episode


def set_f1(expected: Sequence[str], predicted: Sequence[str]) -> float:
    gold = set(expected)
    actual = set(predicted)
    if not gold and not actual:
        return 1.0
    if not gold or not actual:
        return 0.0
    precision = len(gold & actual) / len(actual)
    recall = len(gold & actual) / len(gold)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def edge_f1(
    expected: Sequence[tuple[str, str]], predicted: Sequence[tuple[str, str]]
) -> float:
    return set_f1(
        [f"{left}->{right}" for left, right in expected],
        [f"{left}->{right}" for left, right in predicted],
    )


def evaluate_advisor(
    advisor: Any,
    episodes: Sequence[Episode],
    source_index: Mapping[str, Episode] | None = None,
) -> dict[str, Any]:
    selection = [
        episode
        for episode in episodes
        if episode.output_valid and episode.verified and episode.feedback == "accepted"
    ]
    action_hits = 0
    tool_scores: list[float] = []
    skill_scores: list[float] = []
    edge_scores: list[float] = []
    violated_edges = 0
    mandatory_edges = 0
    known_abstentions = 0
    incompatible_sources = 0
    total_sources = 0

    for episode in selection:
        advice: Advice = advisor.advise(
            episode.command_cues,
            episode.context,
            episode.output_signals,
            repository=episode.repository,
        )
        action_hits += int(advice.action == episode.action)
        known_abstentions += int(advice.abstained)
        tool_scores.append(set_f1(episode.tools, advice.tools))
        skill_scores.append(set_f1(episode.skills, advice.skills))
        edge_scores.append(edge_f1(episode.required_edges, advice.step_edges))
        predicted_edges = set(advice.step_edges)
        mandatory_edges += len(episode.required_edges)
        violated_edges += sum(edge not in predicted_edges for edge in episode.required_edges)
        if source_index is not None:
            for source_id in advice.source_episode_ids:
                source = source_index[source_id]
                total_sources += 1
                incompatible_sources += int(source.context != episode.context)

    invalid = valid = rejected_invalid = rejected_valid = severe_false_acceptance = 0
    for episode in episodes:
        advice = advisor.advise(
            episode.command_cues,
            episode.context,
            episode.output_signals,
            repository=episode.repository,
        )
        if episode.output_valid:
            valid += 1
            rejected_valid += int(advice.reject_output)
        else:
            invalid += 1
            rejected_invalid += int(advice.reject_output)
            if episode.output_severity == "high" and not advice.reject_output:
                severe_false_acceptance += 1

    count = len(selection)
    tool_f1 = mean(tool_scores) if tool_scores else 0.0
    skill_f1 = mean(skill_scores) if skill_scores else 0.0
    return {
        "selection_count": count,
        "action_accuracy": action_hits / count if count else 0.0,
        "tool_set_f1": tool_f1,
        "skill_set_f1": skill_f1,
        "macro_set_f1": mean((tool_f1, skill_f1)),
        "workflow_edge_f1": mean(edge_scores) if edge_scores else 0.0,
        "mandatory_edge_violation_rate": violated_edges / mandatory_edges if mandatory_edges else 0.0,
        "known_abstention_rate": known_abstentions / count if count else 0.0,
        "invalid_output_recall": rejected_invalid / invalid if invalid else 1.0,
        "false_rejection_rate": rejected_valid / valid if valid else 0.0,
        "severe_false_acceptance_count": severe_false_acceptance,
        "cross_context_contamination": incompatible_sources / total_sources if total_sources else 0.0,
    }


def average_metrics(items: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    keys = sorted({key for item in items for key, value in item.items() if isinstance(value, (int, float))})
    return {key: mean(float(item[key]) for item in items) for key in keys}
