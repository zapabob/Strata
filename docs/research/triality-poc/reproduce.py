"""Recompute the supplied three-seed PoC aggregation; no training or file writes."""

import csv
import json
import math
from pathlib import Path
import statistics


def main() -> None:
    root = Path(__file__).resolve().parent
    runs = json.loads((root / "results.json").read_text())["runs"]
    expected = json.loads((root / "summary.json").read_text())
    assert [run["seed"] for run in runs] == [0, 1, 2]
    rows = []
    for arm in runs[0]["arms"]:
        kl = [run["arms"][arm].get("teacher_kl", 0.0) for run in runs]
        nll = [run["arms"][arm]["nll"] for run in runs]
        accuracy = [run["arms"][arm]["accuracy_suffix"] for run in runs]
        rows.append(
            dict(
                arm=arm,
                teacher_kl_mean=statistics.mean(kl),
                teacher_kl_seed_sd=statistics.stdev(kl),
                nll_mean=statistics.mean(nll),
                nll_seed_sd=statistics.stdev(nll),
                pooled_ppl=math.exp(statistics.mean(nll)),
                suffix_accuracy=statistics.mean(accuracy),
            )
        )
    with (root / "tiny_lm_summary.csv").open(newline="") as stream:
        csv_rows = list(csv.DictReader(stream))
    for computed, stored, csv_row in zip(
        rows, expected["table"], csv_rows, strict=True
    ):
        assert computed["arm"] == stored["arm"] == csv_row["arm"]
        for key in computed.keys() - {"arm"}:
            assert math.isclose(
                computed[key], stored[key], rel_tol=1e-12, abs_tol=1e-15
            )
            assert math.isclose(
                computed[key], float(csv_row[key]), rel_tol=1e-12, abs_tol=1e-15
            )
    paired = [
        run["arms"]["triality3x2"]["teacher_kl"]
        - run["arms"]["triality_trained"]["teacher_kl"]
        for run in runs
    ]
    mean = statistics.mean(paired)
    half = 4.302652729696142 * statistics.stdev(paired) / math.sqrt(3)
    interval = [mean - half, mean + half]
    assert all(
        math.isclose(x, y, rel_tol=1e-12)
        for x, y in zip(interval, expected["exploratory_t_ci95"])
    )
    assert interval[0] < 0 < interval[1]
    print(
        json.dumps(
            {
                "verified_table": rows,
                "paired_mean": mean,
                "exploratory_t_ci95": interval,
                "training_rerun": False,
                "original_plot_reproduced": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
