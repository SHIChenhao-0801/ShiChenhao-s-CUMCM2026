from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


root = Path(__file__).resolve().parents[3]
folder = Path(__file__).resolve().parent
source = folder / 'derivations.md'
text = source.read_text(encoding='utf-8')
inventory = json.loads((folder / 'derivation_input_inventory.json').read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


marked = re.findall(r'<!-- (EQ_A_[A-Z0-9_]+) -->\s*\$\$\n(.*?)\n\$\$', text, re.S)
labels = [label for label, equation in marked]
all_labels = re.findall(r'<!-- (EQ_A_[A-Z0-9_]+) -->', text)
all_blocks = re.findall(r'\$\$\n(.*?)\n\$\$', text, re.S)
references = re.findall(r'\[(EQ_A_[A-Z0-9_]+)\]', text)
assert len(marked) == len(all_blocks) == len(all_labels) == 78
assert len(set(labels)) == len(labels)
assert not set(references) - set(labels)
assert text.count('$$') == 2 * len(all_blocks)
equation_checks = []
for label, equation in marked:
    structural = re.sub(r'\\[{}]', '', equation)
    depth = 0
    for character in structural:
        if character == '{':
            depth += 1
        elif character == '}':
            depth -= 1
        assert depth >= 0, label
    assert depth == 0, label
    assert equation.count(r'\left') == equation.count(r'\right'), label
    environments = re.findall(r'\\begin\{([^}]+)\}', equation)
    ends = re.findall(r'\\end\{([^}]+)\}', equation)
    assert sorted(environments) == sorted(ends), label
    equation_checks.append({'label': label, 'latexSha256': hashlib.sha256(equation.encode('utf-8')).hexdigest(),
                            'balancedBracesAndEnvironments': True,
                            'sourceLine': text[:text.index('<!-- ' + label + ' -->')].count('\n') + 1})
headings = re.findall(r'^## (A\.\d+) (.+)$', text, re.M)
assert [number for number, title in headings] == [f'A.{n}' for n in range(1, 21)]
source_checks = []
for item in inventory['sources']:
    source_checks.append({**item, 'unchangedSinceRead': digest(root / item['path']) == item['sha256']})
assert len(source_checks) == 44 and all(item['unchangedSinceRead'] for item in source_checks)
assert digest(root / inventory['paper']['path']) == inventory['paper']['sha256']
references_path = root / 'paper_output/qa/revision_20260913/references/references_verified.json'
reference_metadata = json.loads(references_path.read_text(encoding='utf-8'))
reference_records = [record for record in reference_metadata['references'] if record['number'] in (4, 5, 6, 7)]
assert len(reference_records) == 4
for number in (4, 5, 6, 7):
    assert f'[{number}]' in text
evidence_paths = [
    root / '支撑材料/03_程序代码/numerical_design.txt',
    root / 'paper_output/qa/manuscript_20260912/appendix_derivation_research.md',
    root / 'paper_output/qa/manuscript_20260912/appendix_numerical_process.md',
    root / 'paper_output/final_paper_source.md',
    root / 'paper_output/qa/comment_sandbox_20260913/final_delivery_audit.json',
    root / 'paper_output/qa/comment_sandbox_20260913/verification_work/windows_sandbox_verification_matrix.json',
    references_path,
]
coverage = {
    'dry_basis_and_wet_basis': ['A.1'],
    'dry_and_water_mass_balance': ['A.2', 'A.3', 'A.6'],
    'effective_heat_capacity_not_total_energy': ['A.3', 'A.6', 'A.10', 'A.18'],
    'given_four_question_properties_and_units': ['A.4', 'A.5'],
    'material_vs_fixed_spatial_skeleton_and_grid_velocity': ['A.6', 'A.7'],
    'center_surface_control_volume_weights': ['A.8'],
    'kirchhoff_concentration_potential_and_frozen_face_temperature': ['A.9'],
    'analytic_jacobian_flux_capacity_boundary_and_accumulator': ['A.11'],
    'bdf_newton_ndf_dense_output': ['A.12'],
    'continuous_vs_discrete_maximum_and_strict_report': ['A.13'],
    'physical_positions_moving_boundary_output': ['A.14'],
    'robin_bessel_roots_coefficients_and_time_convolution': ['A.15'],
    'point_vs_cell_average_and_error_metric': ['A.16'],
    'accepted_sensitivity_and_method_comparison_scope': ['A.17', 'A.18', 'A.19'],
    'references_real_metadata_and_support_limits': ['A.20'],
}
reviewed_points = [
    'rho_d conservation subtracts out compression; rho_eff belongs to effective heat capacity, not conserved dry mass.',
    'General moving-grid residual is (v_s-v_g)/R times the material-coordinate gradient; it cancels only for v_s=v_g=r Rdot/R.',
    'Uniform radial shrink at fixed axial length gives rho_d R^2 constant; initial uniform rho_d remains spatially uniform.',
    'Heat capacity times material T derivative is a closure; product differentiation adds capacity and volume terms to a capacity-weighted energy-like quantity.',
    'Center and surface weights are dx^2/8 and dx/2-dx^2/8; total weights equal 1/2.',
    'Production unknowns are approximate nodal point values; cell-average representation has a distinct Bessel projection.',
    'Kirchhoff potential derivative equals exp(-a/C); only the concentration integral is analytic, not the entire temperature-dependent spatial flux.',
    'Near-equal concentration uses a midpoint expression and its own chain-rule derivatives; protected coefficient derivatives differ from raw surface-drive derivatives.',
    'Jacobian includes temperature factor derivatives with 1/2, harmonic k derivatives, rho_eff*cp quotient derivative, Robin surface derivatives and accumulator row.',
    'SciPy BDF uses NDF refinement; the dense polynomial uses saved scale and differences, not a fitted 60-second series.',
    'Strict report uses integer indices on the 0.36-second grid, original precision and actual trajectory queries; root equality alone is not strict feasibility.',
    'Positive finite Robin Biot roots, weighted norms, uniform-function coefficients and piecewise-linear boundary convolution match the benchmark source.',
    'Kp at Cref is defined by continuous extension 1/p; its empirical family is not a calibrated isotherm or a proven physical time bound.',
    'Known historical failed interfaces, false trends and unmet error tolerances remain explicitly unaccepted.',
]
report = {
    'status': 'DERIVATION_SOURCE_AND_STATIC_MATH_REVIEW_COMPLETE',
    'createdAtUtc': datetime.now(timezone.utc).isoformat(),
    'output': {'path': str(source), 'sha256': digest(source), 'characters': len(text), 'lines': len(text.splitlines())},
    'scope': 'Standalone appendix derivations only. No formal PDE/model/source changes, no new numerical experiment, no DOCX construction or rendering by this agent.',
    'paperInput': inventory['paper'],
    'currentSupportSourceReadInventory': source_checks,
    'currentSourceCountRead': 44,
    'additionalDataProcessingAndPlottingSources': 'Root handles the appended three sources; derivation prose points to the final code appendix rather than freezing its file count.',
    'equationCount': len(equation_checks), 'equations': equation_checks,
    'equationReferencesResolved': True, 'duplicateLabels': [], 'headings': headings,
    'coverage': coverage, 'reviewedMathematicalPoints': reviewed_points,
    'independentReviewer': {'agent': '/root/verification_independence/appendix_math_review',
                           'scope': 'Read-only formulas against current core/Jacobian/dense-output/Bessel/analytic-comparison sources, with local SciPy implementation inspection.',
                           'result': 'Formulas and limitations reconciled; no PDE rerun or source mutation.'},
    'rootRequestedCorrectionsApplied': ['Removed dynamic code count from derivation prose',
                                       'Added A.20 four real reference records with limited support statements',
                                       'Split identified long formulas using aligned',
                                       'Explicit continuous extension Kp(Cref)=1/p'],
    'referenceMetadata': [{'number': item['number'], 'key': item['key'], 'bibliography': item['bibliography'],
                           'verification_level': item['verification_level']} for item in reference_records],
    'evidence': [{'path': str(path), 'sha256': digest(path)} for path in evidence_paths],
    'remainingLimits': ['No rigorous full-field error bound or measured internal-temperature/moisture validation is supplied.',
                        'Gas-solid equilibrium mapping, effective heat capacity and internal uniform shrink remain model assumptions.',
                        'Historical high-grid spatial full-second projection arrays were not all retained; appendix does not claim a new replay.',
                        'Empirical closure default script/interface issues remain; no claim all old methods passed.',
                        'LaTeX-to-OMML conversion, DOCX equation numbering, page layout and visual rendering are pending the root document build.',
                        'Team human review is not certified by this mathematical review.'],
    'newExternalSearchPerformed': False,
    'noNewFullTextReadingClaim': True,
    'noGitOperations': True,
}
(folder / 'derivation_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'status': report['status'], 'sections': len(headings), 'equations': len(equation_checks),
                  'sourceFilesUnchanged': len(source_checks), 'characters': len(text),
                  'sha256': digest(source)}, ensure_ascii=False))
