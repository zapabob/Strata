import math

import pytest

from benchmark_inkling2 import aggregate, nll_increase


@pytest.mark.parametrize("new,counts", [(2., (1,0,0)), (8., (0,1,0)), (4., (0,0,1))])
def test_perplexity_direction(new, counts):
    s = nll_increase([dict(reference_ppl=4., candidate_ppl=new)])
    assert (s["improved"], s["worsened"], s["ties"]) == counts
    assert s["mean"] == pytest.approx(math.log(new/4.))


def test_unequal_lengths_are_weighted_by_predicted_tokens():
    def row(n, value):
        return dict(tokens=n, reference_ppl=2., candidate_ppl=value,
                    sum_reference_nll=n*math.log(2.), sum_candidate_nll=n*math.log(value),
                    sum_kl=0., argmax_matches=n)
    result = aggregate({"short":row(1,16.), "long":row(3,1.)})
    assert result["candidate_ppl"] == pytest.approx(2.)
    assert result["delta_nll"] == pytest.approx(0.)
    assert result["total_tokens"] == 4
