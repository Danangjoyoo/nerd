import json
import unittest

from poc.dataset import generate_development_stream, make_raw_episode
from poc.model import (
    BehaviorMemory,
    Episode,
    canonical_json,
    capture_episode,
    chronological_split,
    resolve_current,
)
from poc.runner import run_iteration


class CaptureTests(unittest.TestCase):
    def test_capture_round_trip_redacts_secrets_and_drops_authority(self):
        seeded = [
            "sk-live-abcdefghijklmnopqrstuvwxyz123456",
            "Bearer abcdefghijklmnopqrstuvwxyz012345",
            "correct-horse-battery-staple",
            "-----BEGIN PRIVATE KEY-----",
        ]
        raw = make_raw_episode(
            episode_id="capture-1",
            sequence=1,
            raw_command=(
                "run api tests token=sk-live-abcdefghijklmnopqrstuvwxyz123456 "
                "Authorization: Bearer abcdefghijklmnopqrstuvwxyz012345 "
                "password=correct-horse-battery-staple "
                "-----BEGIN PRIVATE KEY-----"
            ),
            authority="deploy production",
        )
        episode = capture_episode(raw)
        persisted = canonical_json(episode.to_dict())

        self.assertEqual(episode, Episode.from_dict(json.loads(persisted)))
        self.assertNotIn("authority", episode.to_dict())
        self.assertNotIn("raw_command", episode.to_dict())
        for secret in seeded:
            self.assertNotIn(secret, persisted)

    def test_chronological_split_is_disjoint_and_ordered(self):
        episodes = generate_development_stream(11)
        train, calibration, test = chronological_split(episodes)
        ids = [set(item.episode_id for item in part) for part in (train, calibration, test)]

        self.assertFalse(ids[0] & ids[1])
        self.assertFalse(ids[0] & ids[2])
        self.assertFalse(ids[1] & ids[2])
        self.assertLess(max(item.sequence for item in train), min(item.sequence for item in calibration))
        self.assertLess(max(item.sequence for item in calibration), min(item.sequence for item in test))


class LearnerTests(unittest.TestCase):
    def setUp(self):
        stream = generate_development_stream(11)
        self.train, self.calibration, self.test = chronological_split(stream)

    def test_failed_execution_is_not_positive_workflow_evidence(self):
        failed = make_raw_episode(
            episode_id="failed-1",
            sequence=999,
            verified=False,
            feedback="rejected",
            tools=["unsafe-tool"],
        )
        learner = BehaviorMemory(profile=3).fit(
            self.train + [capture_episode(failed)], self.calibration
        )
        advice = learner.advise(
            command_cues=("test", "api"),
            context={"language": "python", "surface": "api", "project_kind": "service"},
        )

        self.assertNotIn("unsafe-tool", advice.tools)
        self.assertNotIn("failed-1", advice.source_episode_ids)

    def test_current_explicit_values_override_advice_outside_learner(self):
        learner = BehaviorMemory(profile=3).fit(self.train, self.calibration)
        advice = learner.advise(
            command_cues=("test", "api"),
            context={"language": "python", "surface": "api", "project_kind": "service"},
        )
        resolved = resolve_current(advice, {"tools": ["user-selected-tool"]})

        self.assertEqual(resolved["tools"], ["user-selected-tool"])
        self.assertEqual(advice.origin, "behavioral_memory_advice")

    def test_context_hybrid_provenance_does_not_cross_context(self):
        learner = BehaviorMemory(profile=2).fit(self.train, self.calibration)
        context = {"language": "typescript", "surface": "browser", "project_kind": "web"}
        advice = learner.advise(command_cues=("diagnose", "failure"), context=context)
        source_by_id = {episode.episode_id: episode for episode in self.train}

        self.assertFalse(advice.abstained)
        for episode_id in advice.source_episode_ids:
            self.assertEqual(source_by_id[episode_id].context, context)

    def test_refined_guard_rejects_high_severity_invalid_output(self):
        learner = BehaviorMemory(profile=3).fit(self.train, self.calibration)
        advice = learner.advise(
            command_cues=("test", "api"),
            context={"language": "python", "surface": "api", "project_kind": "service"},
            output_signals=("secret_leak",),
        )

        self.assertTrue(advice.reject_output)

    def test_refined_model_abstains_on_unknown_command(self):
        learner = BehaviorMemory(profile=3).fit(self.train, self.calibration)
        advice = learner.advise(
            command_cues=("quantum", "teleport"),
            context={"language": "rust", "surface": "satellite", "project_kind": "unknown"},
        )

        self.assertTrue(advice.abstained)

    def test_three_verified_corrections_retire_obsolete_recommendation(self):
        learner = BehaviorMemory(profile=3).fit(self.train, self.calibration)
        context = {"language": "python", "surface": "api", "project_kind": "service"}
        obsolete = learner.advise(("test", "api"), context).tools
        corrections = []
        for index in range(3):
            raw = make_raw_episode(
                episode_id=f"correction-{index}",
                sequence=1000 + index,
                context=context,
                command="test api",
                action="test",
                tools=["uv"],
                steps=["inspect_pytest", "run_uv", "report"],
                skills=["create-unit-tests", "nerd-execute"],
                feedback="corrected",
                corrected_tools=["uv"],
                verified=True,
            )
            corrections.append(capture_episode(raw))
            learner.observe(corrections[-1])

        self.assertLess(learner.obsolete_usage_share("test", context, obsolete), 0.10)


class ReproductionTests(unittest.TestCase):
    def test_iteration_three_is_deterministic_without_timing(self):
        first = run_iteration(3, seeds=(11, 17, 23), include_timing=False)
        second = run_iteration(3, seeds=(11, 17, 23), include_timing=False)

        self.assertEqual(first["canonical_digest"], second["canonical_digest"])
        self.assertEqual(first["metrics"], second["metrics"])


if __name__ == "__main__":
    unittest.main()
