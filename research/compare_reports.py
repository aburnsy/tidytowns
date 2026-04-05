"""Compare category scores between TMB and exemplar villages."""
import sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import fitz

CATEGORIES = [
    'Community',
    'Streetscape',
    'Green Spaces',
    'Nature and Biodiversity',
    'Sustainability',
    'Tidiness and Litter',
    'Residential Streets',
    'Approach Roads',
]

def extract_scores_from_report(filepath):
    """Extract category scores from an adjudication report PDF."""
    doc = fitz.open(filepath)
    text = ''
    for page in doc:
        text += page.get_text()
    doc.close()

    scores = {}
    # Look for the score table - pattern: category name followed by numbers
    # Format varies but typically: Max | 2024 | 2025
    lines = text.split('\n')

    # Find scores - they appear as standalone 2-digit numbers near category names
    # Look for the structured table
    all_numbers = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^\d{1,2}$', stripped):
            num = int(stripped)
            if 10 <= num <= 90:
                all_numbers.append((i, num))

    # The scores typically come in groups of 3 (max, 2024, 2025) per category
    # Let's look for the total mark line as anchor
    total_idx = None
    for i, line in enumerate(lines):
        if 'TOTAL' in line.upper() and 'MARK' in line.upper():
            total_idx = i
            break

    # Also look for Mark/Marc and Centre info
    centre_name = ''
    total_score = 0
    for line in lines:
        if 'Centre:' in line or 'Centre' in line:
            match = re.search(r'Centre:\s*(.+?)(?:\s*Ref:|$)', line)
            if match:
                centre_name = match.group(1).strip()
        if 'Mark:' in line:
            match = re.search(r'Mark:\s*(\d+)', line)
            if match:
                total_score = int(match.group(1))

    # Try extracting from table structure
    # Categories appear in order, each followed by max, prev_year, curr_year scores
    cat_patterns = [
        (r'Community', 'Community'),
        (r'Streetscape', 'Streetscape'),
        (r'Green Spaces', 'Green Spaces'),
        (r'Nature and Biodiversity|Nature & Biodiversity', 'Nature & Biodiversity'),
        (r'Sustainability', 'Sustainability'),
        (r'Tidiness|Litter Control', 'Tidiness & Litter'),
        (r'Residential', 'Residential'),
        (r'Approach Roads', 'Approach Roads'),
    ]

    # Collect all numbers that appear to be scores (2-digit, 10-90 range)
    score_values = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^\d{1,2}$', stripped):
            val = int(stripped)
            if 10 <= val <= 95:
                score_values.append(val)

    # The max marks are: 80, 80, 80, 55, 55, 90, 55, 55 = 550
    # Or new: 80, 80, 80, 80, 80, 90, 55, 55 = 600
    max_marks_550 = [80, 80, 80, 55, 55, 90, 55, 55]
    max_marks_600 = [80, 80, 80, 80, 80, 90, 55, 55]

    # Find where the max marks sequence starts in score_values
    result = {'name': centre_name, 'total': total_score, 'categories': {}}

    for max_marks in [max_marks_550, max_marks_600]:
        for start in range(len(score_values) - len(max_marks) * 3 + 1):
            # Check if max marks match
            potential_max = [score_values[start + j*3] for j in range(8) if start + j*3 < len(score_values)]
            if len(potential_max) >= 8 and potential_max[:8] == max_marks:
                # Found it! Extract prev and current year scores
                for j, cat_name in enumerate(['Community', 'Streetscape', 'Green Spaces',
                                               'Nature & Biodiversity', 'Sustainability',
                                               'Tidiness & Litter', 'Residential', 'Approach Roads']):
                    idx = start + j*3
                    if idx + 2 < len(score_values):
                        result['categories'][cat_name] = {
                            'max': score_values[idx],
                            'prev_year': score_values[idx + 1],
                            'curr_year': score_values[idx + 2]
                        }
                return result

    # Fallback: if we have exactly 24 numbers (8 categories x 3 values), try direct mapping
    if len(score_values) >= 24:
        for j, cat_name in enumerate(['Community', 'Streetscape', 'Green Spaces',
                                       'Nature & Biodiversity', 'Sustainability',
                                       'Tidiness & Litter', 'Residential', 'Approach Roads']):
            idx = j * 3
            if idx + 2 < len(score_values):
                result['categories'][cat_name] = {
                    'max': score_values[idx],
                    'prev_year': score_values[idx + 1],
                    'curr_year': score_values[idx + 2]
                }
        return result

    return result

# Process all reports
reports = {
    'Two Mile Borris (318)': 'research/reports/exemplars/../../../applications/../research/reports/exemplars/2025-silvermines-383.pdf',  # placeholder
}

# TMB scores (from the adjudication report we already have)
tmb = {
    'name': 'Two Mile Borris',
    'total': 318,
    'categories': {
        'Community': {'max': 80, 'prev_year': 43, 'curr_year': 45},
        'Streetscape': {'max': 80, 'prev_year': 39, 'curr_year': 41},
        'Green Spaces': {'max': 80, 'prev_year': 42, 'curr_year': 43},
        'Nature & Biodiversity': {'max': 55, 'prev_year': 28, 'curr_year': 29},
        'Sustainability': {'max': 55, 'prev_year': 16, 'curr_year': 17},
        'Tidiness & Litter': {'max': 90, 'prev_year': 62, 'curr_year': 64},
        'Residential': {'max': 55, 'prev_year': 37, 'curr_year': 38},
        'Approach Roads': {'max': 55, 'prev_year': 40, 'curr_year': 41},
    }
}

exemplar_files = [
    ('Silvermines (383)', 'research/reports/exemplars/2025-silvermines-383.pdf'),
    ('Durrow (392)', 'research/reports/exemplars/2025-durrow-392.pdf'),
    ('Emly (395)', 'research/reports/exemplars/2025-emly-395.pdf'),
    ('Rosscarbery (399)', 'research/reports/exemplars/2025-rosscarbery-399.pdf'),
]

results = [tmb]
for name, filepath in exemplar_files:
    try:
        r = extract_scores_from_report(filepath)
        if not r['name']:
            r['name'] = name
        results.append(r)
        print(f'Extracted: {name} -> total: {r["total"]}, categories: {len(r["categories"])}')
    except Exception as e:
        print(f'Error with {name}: {e}')

# Print comparison table
print('\n=== CATEGORY SCORE COMPARISON (2025) ===')
cats = ['Community', 'Streetscape', 'Green Spaces', 'Nature & Biodiversity',
        'Sustainability', 'Tidiness & Litter', 'Residential', 'Approach Roads']

header = f'{"Category":25s} | {"Max":>4s}'
for r in results:
    name = r.get('name', '?')[:15]
    header += f' | {name:>15s}'
print(header)
print('-' * len(header))

for cat in cats:
    row = f'{cat:25s}'
    max_val = tmb['categories'][cat]['max']
    row += f' | {max_val:4d}'
    for r in results:
        if cat in r.get('categories', {}):
            score = r['categories'][cat]['curr_year']
            pct = score / max_val * 100
            row += f' | {score:4d} ({pct:4.0f}%)'
        else:
            row += f' |     {"?":>10s}'
    print(row)

# Total row
row = f'{"TOTAL":25s} |     '
for r in results:
    total = r.get('total', sum(c['curr_year'] for c in r.get('categories', {}).values()))
    row += f' | {total:>15d}'
print(row)

# Gap analysis
print('\n=== GAP ANALYSIS: TMB vs SILVERMINES (closest Tipp North competitor to beat) ===')
for cat in cats:
    if cat in tmb['categories']:
        tmb_score = tmb['categories'][cat]['curr_year']
        max_val = tmb['categories'][cat]['max']
        # Find silvermines
        for r in results:
            if 'Silvermines' in str(r.get('name', '')):
                if cat in r.get('categories', {}):
                    sv_score = r['categories'][cat]['curr_year']
                    gap = sv_score - tmb_score
                    print(f'{cat:25s}: TMB {tmb_score:2d}/{max_val} vs SM {sv_score:2d}/{max_val} -> Gap: {gap:+3d}')

# Save comparison data
with open('research/analysis/comparison_data.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
