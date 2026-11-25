"""Time to a terminal, visible and parseable AIME response, measured in emitted tokens."""
import argparse
from collections import Counter
from pathlib import Path
import re

from benchmark_generation import digest, read, save
from grade_generation import wilson
from source import atomic_bytes


BUDGETS = (4096, 8192, 16384)


def parse_integer(text):
    last = text.rstrip().splitlines()[-1:] or [""]
    match = re.fullmatch(r"\s*####\s*(\d{1,3})\.?\s*", last[0])
    return int(match[1]) if match else None


def curve(records, horizon):
    """Aalen–Johansen with natural unparseable termination as a competing event."""
    risk = len(records)
    if len({r["id"] for r in records}) != risk or horizon <= 0:
        raise ValueError("Use one independent trajectory per problem in each condition")
    counts = {}
    for r in records:
        if r["time"] <= 0 or r["outcome"] not in ("final","terminal_without_final","censored"):
            raise ValueError("Invalid event observation")
        t = min(r["time"],horizon)
        outcome = r["outcome"] if r["time"] <= horizon else "censored"
        counts.setdefault(t, Counter())[outcome] += 1
    active, final, terminal, km = 1., 0., 0., 1.
    area, previous = 0., 0
    points = []
    for t, c in sorted(counts.items()):
        area += (t-previous)*(1-final)
        final += active*c["final"]/risk
        terminal += active*c["terminal_without_final"]/risk
        active *= 1-(c["final"]+c["terminal_without_final"])/risk
        km *= 1-c["final"]/risk
        points.append(dict(tokens=t, at_risk=risk, finals=c["final"], competing=c["terminal_without_final"],
                           censored=c["censored"], incomplete_probability=1-final,
                           final_cumulative_incidence=final, competing_cumulative_incidence=terminal,
                           cause_specific_km=km))
        risk -= sum(c.values())
        previous = t
    supported = bool(records) and (previous == horizon or active < 1e-12)
    if supported:
        area += (horizon-previous)*(1-final)
    return dict(trajectories=len(records), horizon=horizon, supported_to_horizon=supported, points=points,
                restricted_mean_tokens_without_final=area if supported else None,
                median_tokens_to_final=next((p["tokens"] for p in points if p["final_cumulative_incidence"]>=.5), None))


def summarise(rows,horizon):
    n=len(rows)
    finals=sum(r["outcome"]=="final" for r in rows)
    correct=sum(r["correct"] for r in rows)
    total=sum(r["time"] for r in rows)
    return dict(generated=n, graded_attempts=n, parseable_finals=finals, correct=correct,
                truncated=sum(r["outcome"]=="censored" for r in rows),
                terminal_without_final=sum(r["outcome"]=="terminal_without_final" for r in rows),
                unparseable=sum(r["parsed"] is None for r in rows), total_emitted_tokens=total,
                mean_tokens=total/n if n else None, strict_accuracy=correct/n if n else None,
                visible_completion_rate=finals/n if n else None, accuracy_wilson95=wilson(correct,n),
                completion_wilson95=wilson(finals,n), survival=curve(rows,horizon))


def preserve(src,dst):
    if not dst.exists():
        dst.parent.mkdir(parents=True,exist_ok=True)
        atomic_bytes(dst,src.read_bytes())
    if digest(src)!=digest(dst):
        raise ValueError(f"The original record changed: {src}")


def historical(root):
    baseline=root/"evaluation/aime2025"
    work=root/"evaluation/phase11"
    archive=work/"original-aime"
    for name in ("protocol.json","gold.json","test.jsonl"):
        preserve(baseline/name,archive/name)
    spec,gold=read(archive/"protocol.json"),read(archive/"gold.json")
    result={}
    for arm in ("ablated","official"):
        answers=baseline/arm/"answers"
        if not answers.is_dir(): continue
        rows=[]
        preserve(baseline/arm/"identity.json",archive/arm/"identity.json")
        for key in spec["full"]:
            orig=answers/(key+".json")
            if not orig.exists():continue
            f=archive/arm/"answers"/orig.name
            preserve(orig,f)
            a=read(f)
            if a["key"]!=key or a["input_tokens"]!=len(spec["items"][key]["tokens"]):
                raise ValueError("Wrong historical prompt")
            n=a["output_tokens"]
            ids=a.get("output_ids")
            if a["stop"] not in ("eos","word","limit") or n<=0 or n>4096 or (a["stop"]=="limit" and n!=4096):
                raise ValueError("Unexpected historical stopping record")
            parsed=parse_integer(a["content"])
            status="censored" if a["stop"]=="limit" else ("final" if parsed is not None else "terminal_without_final")
            all_ids=isinstance(ids,list) and len(ids)==n and all(type(x) is int and x>=0 for x in ids)
            rows.append(dict(id=key,time=n,outcome=status,parsed=parsed,correct=status=="final" and parsed==gold[key],
                             exact_output_ids=all_ids, original_stop=a["stop"], original_digest=digest(f)))
        if rows:
            result[arm]=dict(**summarise(rows,4096),items=rows,expected=30,raw_id_coverage=sum(r["exact_output_ids"] for r in rows))
    save(work/"historical-survival.json",dict(estimand="Tokens until the terminal visible final satisfying the frozen last-line integer rule",
         time_resolution="Token count at the end of the recorded response",cohorts=result))
    if result:
        plot(work/"historical-survival.png",result)
    return result


def plot(path, cohorts):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7,3.8),layout="constrained")
    for model,v in cohorts.items():
        points=v["survival"]["points"]
        line,=ax.step([0]+[p["tokens"] for p in points],[1.]+[p["incomplete_probability"] for p in points],
                      where="post",label=f"{'Heretic' if model=='ablated' else 'Official'} PQ2_0 (n={v['generated']})")
        for p in points:
            if p["censored"]:
                ax.plot(p["tokens"],p["incomplete_probability"],"|",color=line.get_color(),ms=10)
                ax.annotate(f"{p['censored']} censored",(p["tokens"],p["incomplete_probability"]),
                            xytext=(-5,-17),textcoords="offset points",ha="right")
    ax.set(xlabel="Cumulative generated tokens",ylabel="Probability of no scorable final",ylim=(0,1.05),xlim=(0,4330))
    ax.legend(loc="lower left")
    fig.savefig(path,dpi=180);plt.close(fig)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("root",type=Path)
    for arm,r in historical(p.parse_args().root).items():
        print(arm,r["correct"],r["generated"],r["total_emitted_tokens"],r["raw_id_coverage"])
