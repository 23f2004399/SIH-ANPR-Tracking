#!/usr/bin/env python3
"""
Standalone ANPR Plate Recognition Evaluator
============================================
Primary engine: fast-plate-ocr (ONNX, plate-specific CTC models, CPU-fast).
Baseline engine: EasyOCR (kept for side-by-side comparison only).

Usage:
    python ocr.py                                  # default model on ./outputs/crops/plates
    python ocr.py path/to/plates/                  # custom folder
    python ocr.py path/to/plate.jpg                # single image
    python ocr.py --compare                        # bake-off across all global models
    python ocr.py --engine easyocr                 # old EasyOCR baseline
    python ocr.py --model cct-xs-v2-global-model   # pick a specific model
    python ocr.py --no-correct                     # raw model output, no format correction
    python ocr.py --gt ground_truth.csv            # score against labels (file,plate)

Install:
    pip install "fast-plate-ocr[onnx]"        # CPU
    pip install "fast-plate-ocr[onnx-gpu]"    # CUDA
"""

import os, sys, glob, re, csv, time, argparse

# fast-plate-ocr global models, roughly best -> fastest.
GLOBAL_MODELS = [
    "cct-s-v2-global-model",
    "cct-xs-v2-global-model",
    "global-plates-mobile-vit-v2-model",
    "cct-s-v1-global-model",
    "cct-xs-v1-global-model",
]
DEFAULT_MODEL = GLOBAL_MODELS[0]

# ---------------------------------------------------------------- Indian plate grammar

# Standard format: <2-letter state><1-2 digit RTO><0-3 letter series><4 digit number>
STATE_CODES = {
    "AN","AP","AR","AS","BR","CG","CH","DD","DL","DN","GA","GJ","HP","HR","JH","JK",
    "KA","KL","LA","LD","MH","ML","MN","MP","MZ","NL","OD","OR","PB","PY","RJ","SK",
    "TN","TR","TS","UK","UA","UP","WB",
}

# Glyph confusions, resolved by whether the slot must be a letter or a digit.
TO_ALPHA = {"0":"O", "1":"I", "2":"Z", "4":"A", "5":"S", "6":"G", "7":"T", "8":"B"}
TO_DIGIT = {"O":"0", "Q":"0", "D":"0", "I":"1", "L":"1", "Z":"2", "A":"4",
            "S":"5", "G":"6", "T":"7", "B":"8"}

# Letter-to-letter confusions. Coercion can't catch these (both sides are already
# letters), so they are only applied to the state field, where a closed vocabulary
# of valid codes tells us whether a substitution actually helped.
LETTER_SIM = {
    "A":"RH4N", "B":"REP8", "C":"GOE", "D":"OQPB", "E":"FBC", "F":"EPT",
    "G":"COQ6", "H":"NMKB", "I":"TLJ1", "J":"ILT", "K":"XRNH", "L":"ICET",
    "M":"NHW", "N":"MHWKRA", "O":"QDCG0", "P":"RFB", "Q":"OGD", "R":"PBKN",
    "S":"5BG", "T":"IY7L", "U":"VWJ", "V":"UWY", "W":"VUM", "X":"KY",
    "Y":"VTX", "Z":"2S",
}

BH_RE = re.compile(r"^\d{2}BH\d{4}[A-Z]{1,2}$")
STD_RE = re.compile(r"^[A-Z]{2}\d{1,2}[A-Z]{0,3}\d{4}$")


def clean(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (text or "").upper())


def _coerce(segment: str, want_alpha: bool):
    """
    Force a segment to letters or digits.
    Returns (fixed, n_substitutions), or None if some character cannot be mapped.
    """
    table = TO_ALPHA if want_alpha else TO_DIGIT
    ok = str.isalpha if want_alpha else str.isdigit
    out, subs = [], 0
    for ch in segment:
        if ok(ch):
            out.append(ch)
        elif ch in table:
            out.append(table[ch]); subs += 1
        else:
            return None                      # e.g. 'M' where a digit must go
    return "".join(out), subs


def _fix_state(state: str, prior: tuple = ()) -> tuple[str, int]:
    """
    Nudge a 2-letter state field onto a real RTO code.

    OCR reliably confuses I/T, K/N, M/N and friends, and coercion can't help
    because both sides are letters. The closed set of state codes is what makes
    this safe: a substitution is only accepted if it lands on a real code.

    Several valid codes are often reachable at the same edit cost (TK -> TR and
    TN are both one substitution), so `prior` — the states this deployment
    actually sees — breaks the tie. Returns (state, n_substitutions).
    """
    a, b = state[0], state[1]
    cands = [(0, state)] if state in STATE_CODES else []
    for cost, pairs in ((1, [(x, b) for x in LETTER_SIM.get(a, "")] +
                            [(a, y) for y in LETTER_SIM.get(b, "")]),
                        (2, [(x, y) for x in LETTER_SIM.get(a, "")
                                    for y in LETTER_SIM.get(b, "")])):
        cands += [(cost, x + y) for x, y in pairs if x + y in STATE_CODES]
    if not cands:
        return state, 0

    # A code this deployment actually sees outranks a cheaper edit to some other
    # state — otherwise a misread that lands on a real-but-wrong code (LA for TN)
    # is accepted at zero cost and never reconsidered.
    if prior and (preferred := [c for c in cands if c[1] in prior]):
        return preferred[0][1], preferred[0][0]
    return cands[0][1], cands[0][0]


def correct_indian_plate(raw: str, prior: tuple = ()) -> tuple[str, bool]:
    """
    Snap a raw OCR read onto the Indian plate grammar.

    Tries every valid <state><rto><series><number> segmentation of this length
    and coerces each slot to letters/digits. A candidate is kept only if every
    character maps cleanly, so a truncated or garbled read is returned as-is
    and flagged invalid rather than being mangled into a plausible-looking lie.

    Returns (text, is_valid_format).
    """
    s = clean(raw)
    if not s:
        return "", False

    if BH_RE.match(s):                       # Bharat-series plates
        return s, True

    best, best_cost = None, None
    for rto_len in (1, 2):
        for ser_len in (0, 1, 2, 3):
            if 2 + rto_len + ser_len + 4 != len(s):
                continue
            i = 0
            parts = []
            for length, want_alpha in ((2, True), (rto_len, False),
                                       (ser_len, True), (4, False)):
                got = _coerce(s[i:i+length], want_alpha)
                if got is None:
                    parts = None
                    break
                parts.append(got); i += length
            if parts is None:
                continue                     # segmentation impossible, try next

            cost = sum(c for _, c in parts)
            state, state_cost = _fix_state(parts[0][0], prior)
            cost += state_cost
            candidate = state + "".join(p for p, _ in parts[1:])
            if state not in STATE_CODES:
                cost += 3                    # strong nudge toward real state codes
            if best_cost is None or cost < best_cost:
                best, best_cost = candidate, cost

    if best is None:                         # no clean segmentation -> don't invent one
        return s, False
    return best, bool(STD_RE.match(best)) and best[:2] in STATE_CODES


# ---------------------------------------------------------------- engines

def run_fast_plate(paths, model_name, device, correct, prior=()):
    """Batch-recognise with fast-plate-ocr. Returns (rows, elapsed_seconds)."""
    from fast_plate_ocr import LicensePlateRecognizer

    recognizer = LicensePlateRecognizer(model_name, device=device)

    t0 = time.perf_counter()
    try:
        preds = recognizer.run(paths, return_confidence=True)
    except Exception as exc:                   # fall back so one bad file can't kill the run
        print(f"[WARN] Batch failed ({exc}); retrying one-by-one.")
        preds = []
        for p in paths:
            try:
                preds.extend(recognizer.run([p], return_confidence=True))
            except Exception as inner:
                print(f"[WARN] {os.path.basename(p)}: {inner}")
                preds.append(None)
    elapsed = time.perf_counter() - t0

    rows = []
    for path, pred in zip(paths, preds):
        if pred is None:
            rows.append(dict(path=path, raw="", plate="", mean_conf=0.0,
                             min_conf=0.0, valid=False))
            continue

        raw = clean(pred.plate)
        # char_probs is a fixed-width numpy array (padded); only the first
        # len(raw) entries line up with real characters.
        cp = pred.char_probs
        probs = (list(cp)[:len(raw)] if cp is not None else []) or [0.0]
        plate, valid = correct_indian_plate(raw, prior) if correct else (raw, False)
        rows.append(dict(
            path=path, raw=raw, plate=plate,
            mean_conf=100.0 * sum(probs) / len(probs),
            min_conf=100.0 * min(probs),
            valid=valid,
        ))
    return rows, elapsed


def run_easyocr(paths, correct, prior=()):
    """Original EasyOCR baseline, kept so we can measure the delta."""
    import cv2, easyocr
    allowlist = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    reader = easyocr.Reader(["en"], gpu=True)

    def variants(img):
        h = img.shape[0]
        pad = max(10, int(h * 0.3))
        img = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
        scale = max(1, 128 / img.shape[0])
        img = cv2.resize(img, (int(img.shape[1]*scale), int(img.shape[0]*scale)),
                         interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        enhanced = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray)
        _, otsu = cv2.threshold(cv2.bilateralFilter(gray, 9, 75, 75), 0, 255,
                                cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return [img,
                cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR),
                cv2.cvtColor(otsu, cv2.COLOR_GRAY2BGR),
                cv2.cvtColor(cv2.bitwise_not(otsu), cv2.COLOR_GRAY2BGR)]

    rows = []
    t0 = time.perf_counter()
    for path in paths:
        img = cv2.imread(path)
        best_text, best_conf = "", 0.0
        if img is not None:
            for variant in variants(img):
                dets = reader.readtext(variant, allowlist=allowlist, detail=1)
                if not dets:
                    continue
                dets.sort(key=lambda d: min(pt[1] for pt in d[0]))   # top-to-bottom
                combined = clean("".join(t for _, t, _ in dets))
                conf = sum(c for _, _, c in dets) / len(dets)
                if len(combined) >= 4 and conf > best_conf:
                    best_text, best_conf = combined, conf
        plate, valid = correct_indian_plate(best_text, prior) if correct else (best_text, False)
        rows.append(dict(path=path, raw=best_text, plate=plate,
                         mean_conf=best_conf * 100, min_conf=best_conf * 100, valid=valid))
    return rows, time.perf_counter() - t0


# ---------------------------------------------------------------- reporting

def collect(target):
    if os.path.isfile(target):
        return [target]
    if os.path.isdir(target):
        return sorted(sum((glob.glob(os.path.join(target, e))
                           for e in ("*.jpg", "*.jpeg", "*.png")), []))
    return []


def load_gt(path):
    """Ground-truth CSV with columns file,plate."""
    if not path or not os.path.isfile(path):
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {r["file"].strip(): clean(r["plate"]) for r in csv.DictReader(f)
                if r.get("file") and r.get("plate")}


def image_size(path):
    try:
        import cv2
        img = cv2.imread(path)
        return f"{img.shape[1]}x{img.shape[0]}" if img is not None else "?"
    except Exception:
        return "?"


def report(label, rows, elapsed, gt, min_conf):
    print(f"\n{'='*88}")
    print(f"  ENGINE: {label}   |   {len(rows)} image(s)   |   "
          f"{elapsed*1000:.0f} ms total ({elapsed/max(1,len(rows))*1000:.1f} ms/plate)")
    print(f"{'='*88}")
    print(f"{'#':<4}{'FILE':<28}{'SIZE':<11}{'RAW':<13}{'CORRECTED':<13}"
          f"{'MEAN':>7}{'MIN':>7}  FMT")
    print("-"*88)

    accepted = hits = scored = 0
    for i, r in enumerate(rows, 1):
        name = os.path.basename(r["path"])
        ok_conf = r["min_conf"] >= min_conf
        accepted += ok_conf
        mark = "OK " if r["valid"] else "-- "
        if gt:
            truth = gt.get(name)
            if truth:
                scored += 1
                good = r["plate"] == truth
                hits += good
                mark = "HIT" if good else f"MISS({truth})"
        print(f"{i:<4}{name:<28}{image_size(r['path']):<11}"
              f"{r['raw'] or '-':<13}{r['plate'] or '-':<13}"
              f"{r['mean_conf']:>6.1f}%{r['min_conf']:>6.1f}%  {mark}"
              f"{'' if ok_conf else '  [below --min_conf]'}")

    print("-"*88)
    valid_n = sum(1 for r in rows if r["valid"])
    print(f"  Read something      : {sum(1 for r in rows if r['plate'])}/{len(rows)}")
    print(f"  Valid Indian format : {valid_n}/{len(rows)}")
    print(f"  Above --min_conf {min_conf:.0f}% : {accepted}/{len(rows)}")
    if scored:
        print(f"  EXACT MATCH vs GT   : {hits}/{scored}  ({100*hits/scored:.1f}%)")
    print(f"{'='*88}")
    return hits, scored


def write_csv(out_csv, rows, engine):
    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file", "size", "engine", "raw", "plate",
                    "mean_conf", "min_conf", "valid_format", "path"])
        for r in rows:
            w.writerow([os.path.basename(r["path"]), image_size(r["path"]), engine,
                        r["raw"], r["plate"], f"{r['mean_conf']:.2f}",
                        f"{r['min_conf']:.2f}", r["valid"], r["path"]])
    print(f"  CSV -> {out_csv}\n")


def main():
    ap = argparse.ArgumentParser(description="ANPR plate recognition evaluator")
    ap.add_argument("target", nargs="?", default="./outputs/crops/plates")
    ap.add_argument("--engine", choices=["fast", "easyocr"], default="fast")
    ap.add_argument("--model", default=DEFAULT_MODEL, choices=GLOBAL_MODELS)
    ap.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    ap.add_argument("--compare", action="store_true",
                    help="run every global model over the same images")
    ap.add_argument("--no-correct", dest="correct", action="store_false",
                    help="skip Indian-format correction, show raw model output")
    ap.add_argument("--min_conf", type=float, default=60.0,
                    help="weakest-character confidence needed to accept a read")
    ap.add_argument("--gt", default="", help="ground-truth CSV with columns file,plate")
    ap.add_argument("--state-prior", default="",
                    help="comma-separated state codes this camera actually sees "
                         "(e.g. TN,KL,KA) — breaks ties when repairing the state field")
    ap.add_argument("--output_csv", default="./outputs/ocr_results.csv")
    args = ap.parse_args()

    prior = tuple(s.strip().upper() for s in args.state_prior.split(",") if s.strip())
    if unknown := [s for s in prior if s not in STATE_CODES]:
        print(f"[WARN] Unknown state code(s) in --state-prior: {', '.join(unknown)}")

    paths = collect(args.target)
    if not paths:
        print(f"[ERROR] No images found at: {args.target}")
        sys.exit(1)
    gt = load_gt(args.gt)
    if args.gt and not gt:
        print(f"[WARN] No usable rows in ground truth: {args.gt}")

    if args.compare:
        summary = []
        for model in GLOBAL_MODELS:
            try:
                rows, elapsed = run_fast_plate(paths, model, args.device, args.correct, prior)
            except Exception as exc:
                print(f"[WARN] {model} failed: {exc}")
                continue
            hits, scored = report(model, rows, elapsed, gt, args.min_conf)
            summary.append((model, sum(1 for r in rows if r["valid"]), hits, scored, elapsed))
        print(f"\n{'='*88}\n  BAKE-OFF SUMMARY\n{'='*88}")
        print(f"{'MODEL':<40}{'VALID FMT':>11}{'GT HITS':>10}{'ms/plate':>11}")
        for model, valid, hits, scored, elapsed in summary:
            gt_col = f"{hits}/{scored}" if scored else "-"
            print(f"{model:<40}{valid:>5}/{len(paths):<5}{gt_col:>10}"
                  f"{elapsed/len(paths)*1000:>11.1f}")
        print(f"{'='*88}\n")
        return

    if args.engine == "easyocr":
        rows, elapsed = run_easyocr(paths, args.correct, prior)
        label = "EasyOCR (baseline)"
    else:
        rows, elapsed = run_fast_plate(paths, args.model, args.device, args.correct, prior)
        label = f"fast-plate-ocr / {args.model}"

    report(label, rows, elapsed, gt, args.min_conf)
    write_csv(args.output_csv, rows, label)


if __name__ == "__main__":
    main()