# Accuracy Report — FIND EVIL! Agent

## Test dataset

| Dataset | Source | Description |
|---|---|---|
| VANKO / surface_physical.E01 | DFIR.training / Ovie Carroll | 119GB Microsoft Surface 3 physical image, Nov 2016 |
| vanko-c-drive.CYLR.7z | Provided with challenge | Cellebrite C-drive extraction |

## Known findings (ground truth for validation)

The VANKO case is a well-known CTF/training dataset with documented findings.
Agent findings are compared against published write-ups.

## Agent performance (preliminary)

| Category | True Positives | False Positives | False Negatives | Notes |
|---|---|---|---|---|
| Suspicious executables | — | — | — | Pending live run on SIFT VM |
| Registry persistence | — | — | — | Pending |
| Logon anomalies | — | — | — | Pending |
| YARA matches | — | — | — | Pending |
| Timeline events | — | — | — | Pending |

*Table will be populated after live investigation run. Preliminary numbers will be added before submission.*

## Known limitations / false positive sources

1. **System binaries flagged by YARA**: Built-in Windows binaries can match generic YARA rules for PE file structure. Agent addresses by checking hash against NSRL whitelist.
2. **Timestamp anomalies**: Clock drift / timezone issues on the image can produce events that appear out of sequence. Agent notes timezone info in system_info and adjusts interpretation.
3. **Encrypted/packed files**: Files packed with common packers may evade signature-based detection. Agent flags these separately.
4. **Volume Shadow Copies**: log2timeline processes VSS snapshots which can produce duplicate events. Agent deduplicates by file hash and notes in `false_positive_notes`.
5. **Registry deleted keys**: python-registry may surface deleted registry entries that were not active at time of incident. Confidence scores are reduced for deleted-key findings.

## Self-correction examples

- Tool `get_logon_events` returns "Security.evtx not found" → agent calls `find_suspicious_executables` to locate the file, then calls `parse_evtx` directly with the discovered path
- `yara_scan` times out → agent retries with narrower `scan_path` (only Users/ dir)
- `run_psort` returns no events → agent checks `get_timeline_status` to confirm log2timeline completed, then retries
