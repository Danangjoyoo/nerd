# Inspect and Apply/Verify Tool Latency Results

This is a tool-only local JSONL RPC benchmark. It contains no LLM, agent,
prompt, or Nerd skill. Fixture setup and resets are excluded from timing.

| Comparison | Case | Baseline p50 | Custom p50 | Change | Baseline p95 | Custom p95 | Result | Requests |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| inspect | inspect-small | 6.639 ms | 0.221 ms | +96.67% | 7.919 ms | 0.260 ms | faster | 1 → 1 |
| inspect | inspect-large | 7.762 ms | 4.563 ms | +41.22% | 8.875 ms | 4.723 ms | faster | 1 → 1 |
| apply_verify | apply-small | 47.474 ms | 47.168 ms | +0.65% | 48.186 ms | 47.740 ms | faster | 2 → 1 |
| apply_verify | apply-large | 103.409 ms | 103.191 ms | +0.21% | 105.388 ms | 107.288 ms | inconclusive | 2 → 1 |

## Proof details

### inspect-small

- Samples: 100 valid paired measurements.
- Median paired saving: 6.434 ms.
- 95% bootstrap interval: [6.397, 6.462] ms.
- Operation p50: 6.565 ms baseline; 0.168 ms custom.
- Spawned processes: 1 baseline; 0 custom.
- Request bytes: 224 baseline; 226 custom.
- Response bytes: 375 baseline; 373 custom.

### inspect-large

- Samples: 100 valid paired measurements.
- Median paired saving: 3.355 ms.
- 95% bootstrap interval: [3.164, 3.806] ms.
- Operation p50: 7.676 ms baseline; 4.507 ms custom.
- Spawned processes: 1 baseline; 0 custom.
- Request bytes: 224 baseline; 226 custom.
- Response bytes: 981 baseline; 980 custom.

### apply-small

- Samples: 100 valid paired measurements.
- Median paired saving: 0.271 ms.
- 95% bootstrap interval: [0.129, 0.412] ms.
- Operation p50: 47.204 ms baseline; 47.042 ms custom.
- Spawned processes: 3 baseline; 3 custom.
- Request bytes: 658 baseline; 467 custom.
- Response bytes: 481 baseline; 376 custom.

### apply-large

- Samples: 100 valid paired measurements.
- Median paired saving: 0.286 ms.
- 95% bootstrap interval: [0.174, 0.412] ms.
- Operation p50: 103.117 ms baseline; 103.049 ms custom.
- Spawned processes: 5 baseline; 5 custom.
- Request bytes: 1937 baseline; 1719 custom.
- Response bytes: 724 baseline; 621 custom.

## Boundary

The baseline and custom routes share this experiment's persistent local
JSONL transport. These values demonstrate local operation and orchestration
latency on the recorded host; they do not measure Codex's private built-in
tool transport or prove agent-level speed.
