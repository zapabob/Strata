"""Assemble two independently attributable, upload-ready GGUF model repositories."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from benchmark_generation import digest, read, save
from source import atomic_bytes, download


FILES = {
    'official': ('Inkling-2-Mini-PQ2_0-GGUF','Inkling-2-Mini-PQ2_0-Baseline.gguf'),
    'ablated': ('Inkling-2-Mini-Heretic-PQ2_0-GGUF','Inkling-2-Mini-Heretic-PQ2_0-Balanced.gguf'),
}
VISION='mmproj-Inkling-2-Mini-F16.gguf'
CODE=Path(__file__).resolve().parent

STRATA_FILES=(
    'engine/include/strata/artifact/gguf_reader.hpp','engine/include/strata/quant/types.hpp',
    'engine/include/strata/inkling2/pq2.hpp','engine/src/quant/types.cpp','engine/src/inkling2/ink_gguf_loader.h',
    'engine/src/inkling2/inkling2_loop.cpp','engine/src/inkling2/cuda/ink_hybrid.cuh','engine/src/inkling2/cuda/ink_moe_cuda.cuh',
    'terminal/strata_cli/launch/adopt.py','terminal/strata_cli/launch/inkling_pq2.py','terminal/strata_cli/launch/cmd.py',
    'terminal/strata_cli/launch/settings.py','terminal/strata_control/models.py','terminal/strata_control/inkling_pq2.py',
    'terminal/strata_control/dsv41_fit.py','terminal/tools/gguf_reader.py')


def strata_runtime(repo):
    git=['git','-C',str(repo),'-c','core.safecrlf=false']
    rev=subprocess.check_output(git+['rev-parse','HEAD']).decode().strip()
    with tempfile.TemporaryDirectory() as temp:
        env=dict(os.environ,GIT_INDEX_FILE=str(Path(temp)/'index'))
        subprocess.run(git+['read-tree',rev],env=env,check=True)
        subprocess.run(git+['add','--',*STRATA_FILES],env=env,check=True)
        patch=subprocess.check_output(git+['diff','--cached','--binary',rev,'--',*STRATA_FILES],env=env)
        required = {'engine/src/inkling2/cuda/ink_moe_cuda.cuh': b'ggml_type == 142',
                    'engine/include/strata/inkling2/pq2.hpp': b'pq2_h128_row',
                    'terminal/strata_cli/launch/cmd.py': b'--inkling-engine'}
        for path, marker in required.items():
            if marker not in subprocess.check_output(git+['show',':'+path],env=env):
                raise ValueError('Missing native PQ2_0 integration in '+path)
        if patch:
            subprocess.run(git+['read-tree',rev],env=env,check=True)
            subprocess.run(git+['apply','--cached','--check','--whitespace=nowarn','-'],input=patch,env=env,check=True)
    return rev,patch


def link(source,destination):
    if destination.exists():
        if not destination.samefile(source):
            raise FileExistsError(f'The staging name already contains another file: {destination}')
    else:
        os.link(source,destination)


def runtime(repo):
    git=['git','-C',str(repo),'-c','core.safecrlf=false']
    rev=subprocess.check_output(git+['rev-parse','HEAD']).decode().strip()
    patch=subprocess.check_output(git+['diff','--no-ext-diff','--binary','HEAD','--',
        'ggml','gguf-py','src','include','tools/llama-bench'])
    needed=[b'ggml/src/ggml-cuda/pq2-prism.cuh',b'src/llama-model-loader.cpp',b'src/spin8-basis.h']
    if not all(name in patch for name in needed):
        raise ValueError('Incomplete native integration patch')
    with tempfile.TemporaryDirectory() as temp:
        env=dict(os.environ,GIT_INDEX_FILE=str(Path(temp)/'index'))
        subprocess.run(git+['read-tree',rev],env=env,check=True)
        subprocess.run(git+['apply','--cached','--check','--whitespace=nowarn','-'],
                       input=patch,env=env,check=True)
    return rev,patch


def model_card(variant, filename, manifest, results, mmlu, speed, measure, long_rows, vision_status, ppl, verified):
    repo=manifest['repository']
    title=('Inkling 2 Mini Heretic Full' if variant=='ablated' else 'Inkling 2 Mini')+' · PQ2_0 GGUF'
    appendix = ('The source author edited the attention and expert weights and released the resulting experts in BF16. '
                'This conversion preserves that source lineage. Refusal behaviour was not independently evaluated here.'
                if variant=='ablated' else
                'Expert weights were reconstructed from the published NVFP4 and MXFP8 values and their scales. '
                'The reference for the numerical comparison runs those reconstructed weights in BF16.')
    audit=manifest['integrity']
    lines=[f'''---
license: apache-2.0
base_model: {repo}
base_model_relation: quantized
pipeline_tag: text-generation
tags:
- gguf
- pq2-0
- mixture-of-experts
- inkling
- llama-cpp
---

# {title}

This is a community conversion of [{repo}](https://huggingface.co/{repo}) for local CPU and CUDA inference. {appendix}

## Files and representation

| File | Bytes | Contents |
|---|---:|---|
| \x60{filename}\x60 | {audit['file_bytes']:,} | Text model, tokenizer and chat template |
| \x60{VISION}\x60 | 639,348,192 | F16 vision projector with auxiliary tensors in their required types |

The text file contains {audit['tensors']} tensors and {audit['parameters']:,} parameters, at {audit['whole_file_bpw']:.4f} bits per weight including its header, metadata and alignment. All 24 physical layers have 128 routed experts. The 48 fused gate/up and down banks use PrismML PQ2_0. Each block stores 128 ternary coefficients in 32 bytes and an FP16 scale in two bytes, giving 2.125 bits per expert weight. The coefficients are −1, 0 and +1. All blocks passed the code audit. Quantisation uses a fixed normalised Hadamard transform of order 128. Dense and auxiliary tensors retain mixed storage, including Q6_K, Q4_K and floating point.

The projector comes from the original checkpoint. All 422 source vision tensors matched byte for byte between the two checkpoints, as did the vision and processor configuration. {vision_status}

## Running the model

Use a runtime that implements both the Inkling recurrent graph and the PrismML PQ2_0 expert product (GGML type 142). The bundled patch applies to the upstream llama.cpp revision in \x60runtime/upstream-revision.txt\x60. On Windows, run the following in an x64 Visual Studio developer PowerShell with Git, Ninja, CMake and a CUDA toolkit supporting SM120. This build was exercised with CUDA 13.5.

\x60\x60\x60powershell
.\\runtime\\build.ps1 -WorkDir .\\inkling-build -CudaArchitecture 120
& .\\inkling-build\\build-sm120\\bin\\llama-completion.exe -m .\\{filename} -ngl 99 -c 2048 -n 32 --temp 0 --no-conversation -p 'A triangle has three sides. A square has'
\x60\x60\x60

For a local chat endpoint, start \x60llama-server\x60 from the same build.

\x60\x60\x60powershell
& .\\inkling-build\\build-sm120\\bin\\llama-server.exe -m .\\{filename} --host 127.0.0.1 --port 8080 -ngl 99 -np 1 -c 4096
\x60\x60\x60

## Patched llama.cpp measurements

The test machine used an NVIDIA GeForce RTX 5060 Ti with 16 GiB of VRAM. The table gives mean tokens per second and sample standard deviation across three native \x60llama-bench\x60 repetitions. The benchmark used full model offload, five CPU threads, batch 128 and microbatch 32.

| Test | Tokens/s |
|---|---:|''']
    for r in speed:
        kind=f"Prefill {r['n_prompt']}" if r['n_prompt'] else f"Decode {r['n_gen']}"
        lines.append(f"| {kind} | {r['avg_ts']:.2f} ± {r['stddev_ts']:.2f} |")
    lines+=['',f"Peak device-wide VRAM sampled once per second was {measure['peak_device_used_bytes']/2**30:.2f} GiB. "
        f"On a fixed zero-shot sample of 32 MMLU elementary mathematics items, next-token four-choice scoring gave {mmlu['correct']}/32. "
        'This sample covers one subject.']
    if ppl:
        lines+=['',f"Across four held-out sequences ({ppl['total_tokens']} scored next tokens), "
            f"the source reference had perplexity {ppl['reference_ppl']:.3f} and the GGUF {ppl['candidate_ppl']:.3f}. "
            f"The mean reference-to-GGUF KL divergence was {ppl['mean_kl']:.4f} nats and next-token argmax agreement was {ppl['top1_agreement']:.1%}. "
            'The corpus is small.']
    if results:
        lines+=['','The following zero-shot pass@1 measurements use greedy free generation and strict final-answer extraction. '
            'GSM8K requires a final numeric answer after four hash characters. MATH-500 uses a final boxed answer with exact or symbolic checking. '
            'The ceilings were 512 and 1,024 generated tokens respectively.','',
            '| Test | Scope | Generated | Scored | Correct | Unparseable | At limit |','|---|---|---:|---:|---:|---:|---:|']
        for name,scope,r in results:
            lines.append(f"| {name} | {scope} | {r['generated']} | {r['scored']} | {r['correct']} | {r['unparseable']} | {r['truncated']} |")
    aime=verified.get('aime')
    if aime:
        lines+=['',f"The AIME 2025 run generated {aime['generated']} responses and scored {aime['scored']}. "
                 f"{aime['correct']} were correct, {aime['truncated']} reached the 4,096-token limit and {aime['unparseable']} had no extractable answer."]
    if verified.get('apex'):
        r=verified['apex']
        lines+=['',f"MathArena Apex 2025 covered all twelve published problems. Local greedy inference generated {r['generated']} "
                f"responses at high reasoning effort with an 8,192-token ceiling. MathArena's non-strict grader scored {r['scored']}. "
                f"{r['correct']} were correct, {r['truncated']} reached the limit and {r['unparseable']} had no parsed answer. "
                f"The observed difference from the developer's 34.4% was {r['observed_minus_publisher_pp']:+.1f} percentage points. "
                "The developer's Apex-specific sampling budget and repetition count could not be established. "
                "[Developer model card](https://thinkingmachines.ai/model-card/inkling-2-mini/)"]
    if long_rows:
        lines+=['','Long-context requests used the Hermes Agent Windows client with real source-file text, three independent receipt codes and dynamic routing. '
            'Recall counts exact label/value pairs in the visible JSON reply. Each row represents one prompt.','',
            '| Input tokens | Output protocol | First visible token (s) | Prefill (tokens/s) | Decode (tokens/s) | Recall |',
            '|---:|---|---:|---:|---:|---:|']
        for name,r in long_rows:
            first=r.get('first_visible_content_seconds')
            t=r['timings']
            lines.append(f"| {r['observed_prompt_tokens']:,} | {name} | {first if first is None else round(first,2)} | "
                f"{t['prompt_per_second']:.2f} | {t['predicted_per_second']:.2f} | {len(r['correct_labels'])}/3 |".replace('| None |','| No visible token |'))
    lines+=['','## Strata native CUDA','',
        'The source patch in this distribution adds packed PQ2_0 experts to the native Inkling engine in zapabob/Strata. Build the included revision and serve this GGUF from the model directory. The commands use CUDA 13.5 on Windows.','',
        '```powershell','.\\runtime\\build.ps1 -Strata -WorkDir .\\inkling-build -CudaArchitecture 120',
        f'python .\\inkling-build\\Strata\\terminal\\strata.py launch --family inkling-2-mini --inkling-engine .\\inkling-build\\strata-sm120\\strata-inkling.exe --model-path .\\{filename} --context 4096','```','']
    perf=verified.get('strata_performance')
    if perf:
        lines.append(f"The separate native Strata CUDA benchmark used a 128-token prefill and 32-token decode across three runs. Mean throughput was {perf['prefill_mean']:.2f} and {perf['decode_mean']:.2f} tokens/s respectively.")
    native=verified.get('strata_service')
    if native:
        lines.append(f"The standard local API was exercised at a slot capacity of {native['context_per_slot']:,}. The short arithmetic request returned a visible reply: {native['visible']}. It matched the expected answer: {native['correct']}.")
    control=verified.get('controlled',{})
    if control:
        lines+=['','## Paired checkpoint and quantisation measurements','',
                'The four conditions use identical token IDs. The official reference reconstructs the published NVFP4/MXFP8 checkpoint for BF16 computation. The Heretic reference starts from its released BF16 weights. The GGUF conditions use patched llama.cpp.','',
                '| Condition | MMLU elementary mathematics |','|---|---:|']
        for rec in control['mathematics'].values():
            lines.append(f"| {rec['engine']} | {rec['correct']}/{rec['n']} |")
        for domain,rec in control.get('domains',{}).items():
            lines.append(f"\n{domain} ({rec['total_tokens']} predicted tokens) had source perplexity {rec['reference_ppl']:.3f} and GGUF perplexity {rec['candidate_ppl']:.3f}, with a token-weighted NLL change of {rec['delta_nll']:+.4f} nats.")
    if verified.get('legacy'):
        legacy=verified['legacy']
        lines+=['',f"Across the original four documents on the official checkpoint, three deteriorated and one improved. Token-weighted NLL increased by {legacy['delta_nll']:.4f} nats. In the Japanese prose passage ({legacy['japanese']['tokens']} targets), perplexity changed from {legacy['japanese']['reference_ppl']:.2f} to {legacy['japanese']['candidate_ppl']:.2f}."]
    if verified.get('head_replay'):
        x=verified['head_replay']
        lines+=['',f"An independent readout from the saved official residual states reproduced the source on {x['tokens']} targets "
                f"with KL {x['kl']:.3g} nats and {x['agreement']:.1%} top-one agreement. Substituting only the deployed Q6_K output head "
                f"changed mean NLL by {x['head_nll']:+.5f} nats per token."]
    if verified.get('added_japanese_gguf'):
        x=verified['added_japanese_gguf']
        lines+=['',f"Three additional, preselected Japanese passages supplied {x['tokens']} prediction targets (45, 46 and 48). "
                f"The GGUF in patched llama.cpp gave token-weighted perplexity {x['ppl']:.3f}."]
    if verified.get('expert_attention'):
        x=verified['expert_attention']
        lines+=['','## Expert and attention interventions','',
                f"All four conditions used the same official Transformers graph and {x['tokens']} next-token targets. "
                "Input embeddings, router and output head retained source precision in each condition.",'',
                '| Weights substituted | Mean NLL (nats/token) |','|---|---:|']
        for k,name in zip('ABCD',('None','Experts only','Attention only','Experts and attention'),strict=True):
            lines.append(f"| {name} | {x['mean_nll'][k]:.5f} |")
        for key,name in (('expert_alone','Experts alone'),('attention_alone','Attention alone'),('interaction','Interaction')):
            v=x['effects'][key];lo,hi=x['document_cluster_95'][key]
            lines.append(f"\n{name} contributed {v:+.5f} nats per token (paired document bootstrap interval {lo:+.5f} to {hi:+.5f}).")
    if verified.get('token_attribution'):
        r=verified['token_attribution']
        lines+=['',f"Exact logit attribution over {r['tokens']} official-checkpoint targets gave a mean distributional KL of {r['means']['kl']:.4f} nats and a mean target-specific contribution of {r['means']['target_specific_nll']:+.4f} nats. These add to the measured NLL change."]
    lines+=['','## Scope and provenance','',
        'The distributed weights use conventional Hadamard quantisation. An earlier matched weight-only experiment found 14 wins in 32 comparisons for adaptive Spin(8), with mean relative gain −0.123% and a 95% interval of [−0.339%, +0.099%]. '
        'These data do not establish a Spin(8)-specific improvement. The source authors did not produce or endorse this conversion. '
        'The llama.cpp measurements used SM120. A100 hardware results are pending.',
        '',f'The source model declares Apache-2.0. The accompanying llama.cpp integration carries its MIT licence. '
        f'The package includes the source revision, tensor-type inventory and file digests. [Source checkpoint](https://huggingface.co/{repo}) · '
        '[Original Inkling model](https://huggingface.co/thinkingmachines/Inkling-2-Mini) · '
        '[PrismML format](https://github.com/PrismML-Eng/Bonsai-demo/blob/main/MODEL-FORMATS.md) · '
        '[GSM8K](https://huggingface.co/datasets/openai/gsm8k) · [MATH-500](https://huggingface.co/datasets/HuggingFaceH4/MATH-500) · '
        '[Math-Verify](https://github.com/huggingface/Math-Verify).','']
    return '\n'.join(lines)


def build(args):
    from collections import Counter
    from huggingface_hub import ModelCard
    root=args.root
    evidence=root/'evaluation'
    stage=root/'huggingface'
    stage.mkdir(exist_ok=True)
    parity=read(evidence/'vision-source-parity.json')
    if parity['matched']!=422 or parity['tensors']!=422 or not all(parity['configurations_equal'].values()):
        raise ValueError('The shared vision projector has not been verified')
    base,patch=runtime(args.llama)
    strata_base,strata_patch=strata_runtime(CODE.parents[1])
    license_file=stage/'apache-2.0.txt'
    if not license_file.exists():
        atomic_bytes(license_file,download('https://www.apache.org/licenses/LICENSE-2.0.txt'))
    licence=license_file.read_bytes()
    if b'Apache License' not in licence or b'END OF TERMS AND CONDITIONS' not in licence:
        raise ValueError('Unexpected Apache licence file')
    shutil.copyfile(CODE/'upload_hf_bundle.py',stage/'upload_hf_bundle.py')
    raws=read(stage/'large-file-digests.json') if (stage/'large-file-digests.json').exists() else {}
    for variant,(slug,name) in FILES.items():
        folder=stage/slug
        rt=folder/'runtime'
        rt.mkdir(parents=True,exist_ok=True)
        models=root/(variant+'-models')
        src=models/'Inkling-2-Mini-PQ2_0-Balanced.gguf'
        manifest=read(models/'Inkling-2-Mini-PQ2_0-Balanced.manifest.json')
        audit=manifest['integrity']
        if src.stat().st_size!=audit['file_bytes'] or not audit['digests_verified'] or audit['code_counts'][3]:
            raise ValueError('Invalid text GGUF audit')
        link(src,folder/name)
        link(root/'official-models'/VISION,folder/VISION)
        counts=Counter(t['type'] for t in manifest['tensors'])
        save(folder/'provenance.json',dict(source_repository=manifest['repository'],source_revision=manifest['revision'],
             profile=manifest['profile'],basis=manifest['basis_selection'],activation_weighted=manifest['activation_weighted'],
             tensor_types=counts,text_integrity=audit,projector_source='thinkingmachines/Inkling-2-Mini',
             vision_comparison=parity,upstream_llama_cpp=base))
        atomic_bytes(folder/'LICENSE',licence)
        atomic_bytes(folder/'.gitattributes',b'*.gguf filter=lfs diff=lfs merge=lfs -text\n')
        atomic_bytes(rt/'inkling-pq2.patch',patch)
        atomic_bytes(rt/'upstream-revision.txt',(base+'\n').encode())
        atomic_bytes(rt/'strata-native.patch',strata_patch)
        atomic_bytes(rt/'strata-revision.txt',(strata_base+'\n').encode())
        shutil.copyfile(CODE.parents[1]/'LICENSE',rt/'LICENSE.Strata')
        shutil.copyfile(CODE/'build_windows_cuda.ps1',rt/'compile-strata.ps1')
        shutil.copyfile(args.llama/'LICENSE',rt/'LICENSE.llama.cpp')
        shutil.copyfile(CODE/'build_hf_runtime.ps1',rt/'build.ps1')
        sources={'speed':evidence/('sm120-'+variant)/'throughput-compact-r1/stdout.txt',
                 'memory':evidence/('sm120-'+variant)/'throughput-compact-r1/measurement.json',
                 'mmlu':evidence/('sm120-'+variant)/'maths-native-r1/score.json'}
        maths=[]
        for suite,display in [('gsm8k','GSM8K'),('math500','MATH-500')]:
            for scope in ['full','pilot']:
                f=evidence/'generative-maths'/(scope+'-summary.json')
                if not f.exists():
                    continue
                rec=read(f)['models'].get(variant,{}).get(suite)
                if rec and rec['n']==rec['expected'] and rec['n']>0:
                    scope_name=('Full test' if scope=='full' else ('Seeded sample' if suite=='gsm8k' else 'Ten per difficulty level'))
                    maths.append((display,scope_name,rec))
                    break
        long_rows=[]
        for protocol in ('open-chat','answer-channel'):
            path=evidence/'hermes-long-context'
            if protocol!='open-chat':
                path=path/protocol
            for target in (98304,131072):
                f=path/variant/f'accepted-{target}.json'
                if f.is_file():
                    r=read(f)
                    if r['timings']['prompt_n']==target and r['timings']['cache_n']==0:
                        long_rows.append((protocol,r))
        visual=evidence/('sm120-'+variant)/'vision-summary.json'
        vision_status=read(visual)['card_sentence'] if visual.is_file() else 'End-to-end image evaluation is pending.'
        pp=evidence/('sm120-'+variant)/'heldout-native-r1/scores.json'
        verified={'hardware':'RTX 5060 Ti 16 GiB','runtime_for_legacy_measurements':'patched llama.cpp CUDA',
                  'mmlu':{k:read(sources['mmlu'])[k] for k in ('count','correct','shots','score','seed')},
                  'generation':[dict(task=n,scope=s,**r) for n,s,r in maths]}
        if (q:=evidence/'aime2025/full-summary.json').is_file():
            s=read(q)
            r=s['models'].get(variant)
            if r and r['n']==s['expected'] and r['n']>0: verified['aime']=r
        if (q:=evidence/'apex2025/scores.json').is_file():
            r=read(q)['models'].get(variant)
            if r and r['scored']==r['expected']==12: verified['apex']=r
        for key,rel,fields in (
            ('strata_service','strata-native/latest.json',('context_per_slot','visible','correct','engine_identity_verified','agent_completed','strata_connect_exit')),
            ('strata_performance','strata-native-kernels/performance.json',('prefill_mean','decode_mean','throughput'))):
            if (q:=evidence/f'sm120-{variant}'/rel).is_file():
                vals=read(q)
                verified[key]={k:vals[k] for k in fields}
        if (q:=evidence/'phase7/four-conditions.json').is_file():
            c=read(q)
            verified['controlled']=dict(mathematics=c['mathematics'],transitions=c['transitions'],items=c['items'],
                 domains={d:{k:r[k] for k in ('total_tokens','reference_ppl','candidate_ppl','delta_nll','mean_kl','top1_agreement')}
                          for d,r in c['ppl'].get(variant,{}).get('domains',{}).items()})
            if 'factorial' in c: verified['controlled']['factorial']=c['factorial']
        if variant=='official':
            if (q:=evidence/'phase8/output-head-only.json').is_file():
                r=read(q)
                if r['source_reproduction_accepted']:
                    s=r['source_reproduction']
                    verified['head_replay']=dict(tokens=s['total_tokens'],kl=s['mean_kl'],agreement=s['top1_agreement'],
                                                  head_nll=r['exact_paired_head_effect']['delta_nll'])
            if (q:=evidence/'phase10/standalone-gguf.json').is_file():
                verified['added_japanese_gguf']=read(q)['japanese_added']
            for profile in ('serial','matched'):
                q=evidence/'phase10'/profile/'factorial-results.json'
                if q.is_file():
                    r=read(q)
                    if r['eligible_for_interpretation']:
                        verified['expert_attention']=r['dynamic']['factorial']['all']
                        verified['expert_attention_profile']=r['condition_batching']
                        break
            if (q:=evidence/'phase7/baseline-20261125-1024-jst/corrected-official.json').is_file():
                x=read(q)
                verified['legacy']=dict(delta_nll=x['delta_nll'],japanese=x['sequences']['holdout-2'])
            if (q:=evidence/'phase8/official-token-attribution.json').is_file():
                verified['token_attribution']=read(q)['overall']
        save(folder/'benchmarks.json',verified)
        card=model_card(variant,name,manifest,maths,read(sources['mmlu']),read(sources['speed']),
                 read(sources['memory']),long_rows,vision_status,read(pp) if pp.is_file() else None,verified)
        atomic_bytes(folder/'README.md',card.encode('utf8'))
        parsed=ModelCard.load(folder/'README.md').data.to_dict()
        if parsed['base_model']!=manifest['repository'] or parsed['license']!='apache-2.0' or parsed['base_model_relation']!='quantized':
            raise ValueError('Invalid Hub model-card metadata')
        sums={}
        paths=[folder/n for n in (name,VISION,'README.md','LICENSE','.gitattributes','provenance.json',
               'benchmarks.json','runtime/build.ps1','runtime/inkling-pq2.patch','runtime/upstream-revision.txt','runtime/LICENSE.llama.cpp',
               'runtime/compile-strata.ps1','runtime/strata-native.patch','runtime/strata-revision.txt','runtime/LICENSE.Strata')]
        for path in paths:
            if path.suffix=='.gguf':
                st=path.stat()
                key=f'{st.st_dev}/{st.st_ino}/{st.st_size}/{st.st_mtime_ns}'
                if key not in raws:
                    raws[key]=digest(path)
                    save(stage/'large-file-digests.json',raws)
                value=raws[key]
                if path.name==VISION and value!=parity['projector_sha256']:
                    raise ValueError('Projector bytes differ from the audited projector')
            else:
                value=digest(path)
            sums[path.relative_to(folder).as_posix()]=value
        atomic_bytes(folder/'SHA256SUMS',''.join(f'{v}  {k}\n' for k,v in sorted(sums.items())).encode())
        print(slug, 'ready:',len(sums)+1,'files;',audit['file_bytes'],'text GGUF bytes',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--llama',type=Path,required=True)
    args=parser.parse_args()
    from filelock import FileLock
    with FileLock(str(args.root/'huggingface.prepare.lock')):
        build(args)
