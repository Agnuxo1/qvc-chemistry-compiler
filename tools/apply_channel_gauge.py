# SPDX-FileCopyrightText: 2026 Francisco Angulo de Lafuente
# SPDX-License-Identifier: MIT OR Apache-2.0
# QVC Chemistry Compiler | 2026-11-10 | ORCID 0009-0001-1634-7063
"""Apply a channel rotation, preserving the angle circuits and physical Gram matrix."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import numpy as np
from reconstruir_quimica import write_portable_npz


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=Path, required=True)
    parser.add_argument('--rotation', type=Path, required=True)
    parser.add_argument('--base', type=Path, required=True, help='Matching angle circuits and submission metadata')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    with np.load(args.seed, allow_pickle=False) as archive:
        seed = {key: np.array(archive[key]) for key in archive.files}
    with np.load(args.base / 'submission.npz', allow_pickle=False) as archive:
        output = {key: np.array(archive[key]) for key in archive.files}
    # The compiler encodes angle_words after fitting. Keep the validated base's
    # words and circuits together; compare all physical non-channel inputs.
    for key in output.keys() - {'W', 'H2_I', 'angle_words'}:
        assert np.array_equal(output[key], seed[key]), key
    rotation = np.load(args.rotation, allow_pickle=False)
    groups, _, channels = seed['W'].shape
    assert rotation.shape == (groups, channels, channels)
    orthogonality = float(np.max(np.abs(rotation.transpose(0, 2, 1) @ rotation - np.eye(channels))))
    before = np.concatenate([seed['W'], seed['H2_I'][:, None]], axis=1)
    after = before @ rotation
    drift = float(np.max(np.abs(after @ after.transpose(0, 2, 1) - before @ before.transpose(0, 2, 1))))
    assert orthogonality < 1e-10 and drift < 1e-10
    output.update(W=after[:, :-1], H2_I=after[:, -1])
    args.out.mkdir(parents=True)
    circuits = list(args.base.glob('angle_k_*.kmb'))
    assert len(circuits) == 15
    for path in circuits:
        shutil.copy2(path, args.out / path.name)
    write_portable_npz(args.out / 'submission.npz', output)
    report = {
        'status': 'GAUGE_REBUILT_REQUIRES_FULL_NATIVE_CHECK',
        'source_sha256': sha(Path(__file__)), 'seed_sha256': sha(args.seed),
        'rotation_sha256': sha(args.rotation), 'orthogonality_max_error': orthogonality,
        'augmented_gram_max_drift': drift,
        'baseline_lambda_h2': float(.25 * np.sum(np.abs(before).sum(1) ** 2)),
        'candidate_lambda_h2': float(.25 * np.sum(np.abs(after).sum(1) ** 2)),
        'output_sha256': {path.name: sha(path) for path in args.out.iterdir()},
    }
    report_path = args.out.parent / (args.out.name + '-gauge-proof.json')
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key != 'output_sha256'}))


if __name__ == '__main__':
    main()
