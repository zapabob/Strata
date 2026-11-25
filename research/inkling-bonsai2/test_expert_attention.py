import math

import numpy as np
import pytest

from expert_attention import paired_effects
from factorial_report import per_token


def test_interaction_and_paired_unequal_denominators():
    rows=[dict(A=2.,B=5.,C=1.,D=11.),dict(A=12.,B=15.,C=9.,D=21.)]
    r=paired_effects(rows,[2,6])
    assert r["mean_nll"]["A"]==1.75
    assert r["effects"]["expert_alone"]==.75
    assert r["effects"]["attention_alone"]==-.5
    assert r["effects"]["interaction"]==2.
    assert r["effects"]["joint"]==2.25
    assert r["effects"]["average_expert"]+r["effects"]["average_attention"]==r["effects"]["joint"]
    assert paired_effects(rows[:1],[2])["document_cluster_95"] is None


def test_target_position_and_shared_logit_offset():
    z=np.array([[1.,2.,3.],[2.,3.,4.],[-9.,3.,0.]])
    rows=per_token(z,z+5,[2,0,1])
    assert len(rows)==2
    assert rows[0]["target"]==0 and rows[1]["position"]==1
    assert all(r["source_nll"]==pytest.approx(r["nll"]) and abs(r["kl"])<1e-12 for r in rows)


def test_pooled_hidden_distortion_uses_reference_energy():
    from benchmark_inkling2 import hidden
    from factorial_report import pool_visits
    def bf(x):
        return (np.array(x,dtype=np.float32).view(np.uint32)>>16).astype(np.uint16)
    def doc(x,y):
        h=hidden(bf(x),bf(y))
        margin=dict(reference_mean=1.,candidate_mean=.5)
        return dict(tokens=len(x),visits=[dict(layer=i,visit=0,**h,attention_output=h,expert_mixture=h,
                  dynamic_router_overlap=.5,applied_top8_overlap=1.,routing_margin=margin,router_logit_margin=margin)
                  for i in range(48)])
    p=pool_visits({"a":doc([2.],[1.]),"b":doc([4.,4.],[4.,4.])})
    assert len(p)==48 and p[0]["prediction_positions"]==3
    assert p[0]["hidden"]["relative_l2"]==pytest.approx(1/6)
    assert p[0]["expert_mixture"]["mse"]==pytest.approx(1/3)


def test_benchmark_counts_retain_scored_truncations_without_final_answers():
    from grade_generation import stats
    rows=[dict(correct=True,extracted="2",method="numeric",limit=False,empty=False,tokens=2),
          dict(correct=False,extracted=None,method="missing-final",limit=True,empty=True,tokens=512)]
    report=stats(rows)
    assert [report[k] for k in ("generated","scored","correct","truncated","unparseable")]==[2,2,1,1,1]


def test_logical_components_and_packed_gate_up(tmp_path,monkeypatch):
    import torch
    from decoded_reference import COMPONENTS,DecodedOfficial,OfficialSafetensors,components
    from spin8_quantizer import pack
    rows,width=6,128
    rng=np.random.default_rng(71)
    values=rng.integers(-1,2,(rows,width))
    block=pack(values,np.ones(rows))
    path=tmp_path/"rows.bin"
    path.write_bytes(block.tobytes())
    original=torch.full((1,rows,width),8.,dtype=torch.bfloat16)
    monkeypatch.setattr(OfficialSafetensors,"read",lambda *a:original.clone())
    g=DecodedOfficial.__new__(DecodedOfficial)
    key="model.llm.layers.0.mlp.experts.w13_weight"
    g.path=path
    g.entries={key:dict(raw=key,type="PQ2_0",shape=[1,rows,width],offset=0,bytes=block.nbytes)}
    g.logical={key:{"gate","up"}}
    g.physical={key:dict(origin=[1,rows,width],dtype="BF16")}
    g.restored=set()
    had=np.array([[(-1)**(i&j).bit_count() for j in range(width)] for i in range(width)])/math.sqrt(width)
    g.h=torch.from_numpy(np.sign(had).astype(np.float32));g.matrices={}
    expected=torch.tensor((values@np.sign(had))/math.sqrt(width),dtype=torch.bfloat16)
    for mode in ("gate","up","experts","restore-gate","restore-up","attention","experts-attention"):
        g.enabled=components(mode)
        measured=g.read(key,"cpu",0,1)[0]
        for i,proj in enumerate(("gate","up")):
            expected_slice=expected[i*3:(i+1)*3] if proj in g.enabled else original[0,i::2]
            torch.testing.assert_close(measured[i::2],expected_slice,rtol=0,atol=0)
        if not mode.startswith("restore-"):
            assert components("restore-"+mode)==COMPONENTS-g.enabled
