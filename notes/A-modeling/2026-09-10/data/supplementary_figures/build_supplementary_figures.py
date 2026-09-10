"""Replot frozen evidence only; never import or run a PDE solver.

Run from the 2026CUMCM root with C:/Python314/python.exe -B.
All new output stays beside this driver. Main modeling code and gate inputs
are read-only. Visual acceptance is recorded separately after PNG/PDF review.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
if ROOT.name != '2026CUMCM' or not OUT.is_relative_to(ROOT):
    raise RuntimeError('Use the authorized competition workspace as cwd')
sys.path.insert(0, str(ROOT / 'paper_output/code/modeling'))
import numpy as np
from publication_plots import (make_convergence_plot,
                               make_shrinkage_comparison,
                               make_sensitivity_plot)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record(path):
    path = Path(path)
    return {'path': path.relative_to(ROOT).as_posix(),
            'bytes': path.stat().st_size, 'sha256': sha(path)}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save_csv(name, rows):
    path = OUT / name
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return record(path)


def main():
    sources = ROOT / 'paper_output/results'
    conv_paths = [sources / 'convergence' / name / 'convergence_report.json'
                  for name in ['Q1_K_analytic_J_v3',
                               'Q23_final_resolution_v5',
                               'Q4_final_resolution_v5']]
    experiments = sources / 'experiments'
    fixed = experiments / 'physical_Q4_fixed_N200_K/summary.json'
    shrunk = experiments / 'grids_Q4_N200_K/summary.json'
    scenarios = {
        '平台延拓（基准）': experiments / 'grids_Q23_N200_K/summary.json',
        '4 h 后改为 49 °C': experiments / 'physical_Q23_T49_N200_K/summary.json',
        '4 h 后改为 51 °C': experiments / 'physical_Q23_T51_N200_K/summary.json',
        '4 h 后延续末值': experiments / 'physical_Q23_last_N200_K/summary.json',
        '4 h 后延续末 1 h 均值': experiments / 'physical_Q23_mean_N200_K/summary.json',
    }
    input_paths = conv_paths + [fixed, shrunk] + list(scenarios.values())
    inputs_before = [record(path) for path in input_paths]
    frozen_before = [record(path) for path in sorted((ROOT / 'paper_output/code/modeling').glob('*.py'))]
    plot_module = ROOT / 'paper_output/code/modeling/publication_plots.py'
    assert sha(plot_module) == 'a58b5bb7300aef7f334e28cb0be070971d1681b516e537b84320577b00293388'
    figures = [make_convergence_plot(conv_paths, OUT),
               make_shrinkage_comparison(fixed, shrunk, OUT),
               make_sensitivity_plot(scenarios, OUT, question_id='Q3',
                                     baseline_label='平台延拓（基准）')]

    # Independently reopen sources and emitted plot data, compare every value.
    # Event differences are also archived to CSV; the original helper's NPZ
    # archives the left panel only.
    conv_rows = []
    with np.load(ROOT / figures[0]['plot_data']['path'], allow_pickle=False) as plotted:
        for path in conv_paths:
            source = read(path)
            q = source['question']
            comp = source['comparisons']
            np.testing.assert_array_equal(plotted[q + '_fine_N'], [x['fine_N'] for x in comp])
            np.testing.assert_array_equal(plotted[q + '_C_difference'], [x['max_absolute_difference']['C'] for x in comp])
            for item in comp:
                assert item['radial_count'] == 21
                conv_rows.append({
                    'question': q, 'coarse_N': item['coarse_N'], 'fine_N': item['fine_N'],
                    'maximum_C_difference_kg_kg': item['max_absolute_difference']['C'],
                    'maximum_T_difference_K': item['max_absolute_difference']['T_K'],
                    'event_difference_fine_minus_coarse_s': item['event_difference_s'],
                    'compared_integer_time_count': item['compared_time_count'],
                    'physical_radial_count': item['radial_count'],
                    'C_maximum_difference_time_s': item['locations']['C']['time_s'],
                    'C_maximum_difference_radius_m': item['locations']['C']['radius_m'],
                    'source_path': path.relative_to(ROOT).as_posix(),
                    'source_sha256': sha(path),
                    'solver_sha256': source['runs'][0]['code']['sha256'],
                })

    fixed_source, shrunk_source = read(fixed), read(shrunk)
    differences = {key for key in fixed_source['settings']
                   if fixed_source['settings'][key] != shrunk_source['settings'][key]}
    assert differences == {'shrink'}
    assert fixed_source['code']['sha256'] == shrunk_source['code']['sha256']
    expected_shrink = np.array([fixed_source['diagnostics']['event_h'],
                               shrunk_source['diagnostics']['event_h']])
    with np.load(ROOT / figures[1]['plot_data']['path'], allow_pickle=False) as plotted:
        np.testing.assert_array_equal(plotted['event_hours'], expected_shrink)
    shrink_rows = [{'case': name, 'N': source['settings']['intervals'],
                    'event_h': source['diagnostics']['event_h'],
                    'source_path': path.relative_to(ROOT).as_posix(), 'source_sha256': sha(path),
                    'solver_sha256': source['code']['sha256']}
                   for name, source, path in [('fixed', fixed_source, fixed), ('shrinking', shrunk_source, shrunk)]]

    base = read(next(iter(scenarios.values())))
    sensitivity_rows = []
    for label, path in scenarios.items():
        source = read(path)
        changed = {key for key in base['settings'] if source['settings'][key] != base['settings'][key]}
        assert changed <= {'boundary_extension', 'tail_temperature_C'}
        assert source['settings']['intervals'] == 200
        assert source['code']['sha256'] == base['code']['sha256']
        sensitivity_rows.append({
            'scenario': label, 'N': source['settings']['intervals'],
            'event_h': source['diagnostics']['event_h'],
            'relative_change_percent': 100 * (source['diagnostics']['event_h'] / base['diagnostics']['event_h'] - 1),
            'changed_settings': ','.join(sorted(changed)),
            'source_path': path.relative_to(ROOT).as_posix(), 'source_sha256': sha(path),
            'solver_sha256': source['code']['sha256'],
        })
    with np.load(ROOT / figures[2]['plot_data']['path'], allow_pickle=False) as plotted:
        np.testing.assert_array_equal(plotted['event_hours'], [x['event_h'] for x in sensitivity_rows])
        np.testing.assert_array_equal(plotted['relative_change_percent'], [x['relative_change_percent'] for x in sensitivity_rows])
    csv_records = [save_csv('convergence_plotted_values.csv', conv_rows),
                   save_csv('shrinkage_plotted_values.csv', shrink_rows),
                   save_csv('environment_plotted_values.csv', sensitivity_rows)]
    assert inputs_before == [record(path) for path in input_paths]
    assert frozen_before == [record(path) for path in sorted((ROOT / 'paper_output/code/modeling').glob('*.py'))]
    report = {
        'status': 'COMPUTED_READBACK_EXACT_VISUAL_REVIEW_PENDING',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'scope': 'Existing saved results only; no new PDE solve; supplementary figures outside formal gate inputs.',
        'figure_records': figures, 'plot_value_csvs': csv_records,
        'input_records': inputs_before, 'frozen_modeling_code_records': frozen_before,
        'inputs_and_frozen_code_unchanged': True,
        'readback': {'all_npz_values_equal_reopened_sources': True,
                     'convergence_comparisons': len(conv_rows), 'shrinkage_cases': 2,
                     'environment_cases': len(sensitivity_rows),
                     'grid_sample_scope': 'every integer second on 21 fixed physical radii; finite common domain only',
                     'grid_full_field_error_bound_claimed': False,
                     'sensitivity_confidence_interval_claimed': False},
        'shrinkage_reduction_percent': float(100 * (1 - expected_shrink[1] / expected_shrink[0])),
        'visual_review': 'pending', 'human_review': 'pending', 'new_driver_VS_reproduction': 'pending',
        'driver': record(__file__),
    }
    path = OUT / 'generation_and_value_verification.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({'report': record(path), 'figure_count': len(figures),
                      'PDE_solves': 0, 'inputs_and_frozen_code_unchanged': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()
