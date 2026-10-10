"""Read-only comparison of the Day 7A release, source guards and 42 rows."""

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from scripts.day6a_integrity_check import inspect
    original = inspect()  # Function only: never writes a previous-stage report.
    pinned = json.loads((ROOT / 'docs/day8a_day7a_baseline.json').read_bytes())
    changed = [name for name, value in pinned['files_sha256'].items()
               if not (ROOT/name).is_file() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != value]
    unexpected = sorted(set(changed) - set(pinned['allowed_modified_files']))
    old = json.loads((ROOT/'docs/day7a_preview_matrix_results.json').read_bytes())['cases']
    new = json.loads((ROOT/'docs/day8a_preview_matrix_results.json').read_bytes())['cases']
    old_hashes={(r['hexagram_id'],r['line_position']):r['result_sha256'] for r in old}
    new_hashes={(r['hexagram_id'],r['line_position']):r['result_sha256'] for r in new}
    result = {
        'day7a_commit': pinned['git_commit'], 'day7a_tracked_files': len(pinned['files_sha256']),
        'intentional_transport_or_display_changes': changed, 'unexpected_day7a_changes': unexpected,
        'frozen_engines_reviews_source_and_frames_unchanged_since_day7a': not unexpected,
        'files_differing_from_older_day5_baseline': original['modified_day5_files'],
        'production_files': original['production_files'], 'changed_production_files': original['changed_production_files'],
        'signed_cache_files': original['signed_cache_files'], 'changed_signed_cache_files': original['changed_signed_cache_files'],
        'history_rows': original['history_rows'],
        **{k:original[k] for k in ('history_schema_unchanged','history_row_hashes_unchanged','history_database_bytes_unchanged')},
        'all_384_public_result_hashes_equal_day7a': len(new_hashes)==384 and new_hashes==old_hashes,
        'git_safety': original['git_safety'], 'real_ai_calls':0,
    }
    # Day 7A had already changed the main/UI integration from Day 5. Preserve
    # the actual Day 7A release, while retaining the original production check.
    result['passed'] = (not unexpected and not original['changed_production_files']
        and not original['changed_signed_cache_files'] and original['git_safety']['passed']
        and original['history_rows']==42 and all(original[k] for k in
            ('history_schema_unchanged','history_row_hashes_unchanged','history_database_bytes_unchanged'))
        and result['all_384_public_result_hashes_equal_day7a'])
    (ROOT/'docs/day8a_integrity_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
    return int(not result['passed'])


if __name__=='__main__':raise SystemExit(main())
