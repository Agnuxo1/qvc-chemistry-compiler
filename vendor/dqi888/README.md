# Rebuildable 888-qubit DQI repair

Local derivative research bank; not an independent scientific dataset.
Run with Python3.12 and stock Kickmix1.0.0 (NumPy2.2.6/SciPy1.15.3 environment):

```console
python rebuild_dqi.py --policy repair --runtime stock --out rebuilt-dqi
```

The rebuild reads authenticated text sources only, no input KMB. An independent
stock rebuild already matched the selected bytes from our earlier fork build.
The control policy reproduces the public889-qubit source bytes exactly.

Three complete102400-shot checks passed: stock and fork at the same seed
2026102801 (entire result dictionaries identical), and fork at independent seed
20261029181. Two known value/phase cases pass2048 targeted replicas across both
runtimes. A fresh36-weight grid passes9216 diagnostic shots. Targeted checks are
biased diagnostics, not unbiased error estimates or a universal proof. The raw
public889 circuit fails512/512 phase replicas in each runtime and is not selected.
Official verifier SHA and exact source/circuit hashes are bound in the manifest.
The Windows spawn scheduler is an explicit adaptation, not an unmodified Linux
CLI invocation. No hosted Kaggle run or competition submission is claimed.
