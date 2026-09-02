from __future__ import annotations
import json
from diff2tweet.git import GitContext

JUDGE_PROMPT = '''Tu es un Juge Build in Public. Note de 1 a 10 si ce diff merite un tweet.

10 = grosse feature visible, perf x10, nouveau browser Rust qui tue Chrome
7-9 = feature utile (auth Google auto, fix galere)
4-6 = refacto, petit fix, pas sexy
1-3 = typo, wip, config, bump deps

Reponds UNIQUEMENT JSON {\"score\": 7, \"reason\": \"...\"}
Commit range: {commit_range}
Diff (tronque 4000 chars):
{diff}
'''

def judge_score(config, git_context: GitContext) -> tuple[int, str]:
    if not getattr(config, 'judge_enabled', False):
        return 10, 'judge disabled'
    # fallback heuristique si pas de LLM
    diff = git_context.diff_text[:4000].lower()
    if any(x in diff for x in ['readme', 'typo', 'bump', 'chore(deps)']):
        return 3, 'heuristic: docs/typo/deps'
    if 'auth' in diff or 'rust' in diff or 'browser' in diff:
        return 8, 'heuristic: feature visible'
    return 7, 'heuristic: default pass'
