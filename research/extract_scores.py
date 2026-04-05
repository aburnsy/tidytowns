"""Extract all Category B scores from TidyTowns results booklets (2019-2025)."""
import sys, io, json, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import fitz

COUNTY_NAMES = [
    'CARLOW', 'CAVAN', 'CLARE', 'CORK NORTH', 'CORK SOUTH', 'CORK WEST',
    'DONEGAL', 'DUBLIN', 'GALWAY', 'KERRY', 'KILDARE', 'KILKENNY',
    'LAOIS', 'LEITRIM', 'LIMERICK', 'LONGFORD', 'LOUTH', 'MAYO', 'MEATH',
    'MONAGHAN', 'OFFALY', 'ROSCOMMON', 'SLIGO',
    'TIPPERARY NORTH', 'TIPPERARY SOUTH',
    'WATERFORD', 'WESTMEATH', 'WEXFORD', 'WICKLOW'
]

def normalize_county(text):
    """Normalize county name from various formats."""
    text = text.upper().strip()
    text = text.replace('(NORTH)', 'NORTH').replace('(SOUTH)', 'SOUTH').replace('(WEST)', 'WEST')
    text = re.sub(r'\s*[-–]\s*.*$', '', text)  # Remove Irish name
    text = text.strip()
    for cn in COUNTY_NAMES:
        if cn in text:
            return cn
    return None

def extract_from_booklet(filepath, year):
    """Extract all entries with scores, grouped by category."""
    doc = fitz.open(filepath)
    results = []

    for page_num in range(len(doc)):
        text = doc[page_num].get_text()
        if 'ANALYSIS' not in text and 'Category' not in text:
            continue

        lines = [l.strip() for l in text.split('\n')]
        current_county = None
        current_category = None
        pending_name = None
        pending_award = ''

        for i, line in enumerate(lines):
            if not line:
                continue

            # Detect county header
            county = normalize_county(line)
            if county and len(line) > 5 and not line.isdigit():
                current_county = county
                current_category = None
                pending_name = None
                continue

            # Detect category
            cat_match = re.match(r'^Category\s+([A-H])', line)
            if cat_match:
                current_category = cat_match.group(1)
                pending_name = None
                continue

            if not current_county or not current_category:
                continue

            # Is this line a score (3-digit number)?
            if re.match(r'^\d{3}$', line):
                score = int(line)
                if 150 <= score <= 450 and pending_name:
                    results.append({
                        'year': year,
                        'county': current_county,
                        'category': current_category,
                        'village': pending_name,
                        'score': score,
                        'award': pending_award
                    })
                    pending_name = None
                    pending_award = ''
                continue

            # Is this line an award?
            if any(kw in line for kw in ['County First', 'County Second', 'County Third',
                                          'Gold Medal', 'Silver Medal', 'Bronze Medal',
                                          'Endeavour Award']):
                award_parts = []
                if 'County First' in line: award_parts.append('County 1st')
                elif 'County Second' in line: award_parts.append('County 2nd')
                elif 'County Third' in line: award_parts.append('County 3rd')
                if 'Gold' in line: award_parts.append('Gold')
                elif 'Silver' in line: award_parts.append('Silver')
                elif 'Bronze' in line: award_parts.append('Bronze')
                if 'Endeavour' in line: award_parts.append('Endeavour')
                # This award belongs to the PREVIOUS entry
                if results and not pending_name:
                    results[-1]['award'] = ' & '.join(award_parts)
                else:
                    pending_award = ' & '.join(award_parts)
                continue

            # Is this a village name? (contains ' - ' for Irish translation, or is a proper name)
            if ' - ' in line and not line.startswith('Centre') and not line.startswith('Mark') and not line.startswith('Award'):
                # Extract English name (before the dash)
                name = line.split(' - ')[0].strip()
                if len(name) > 2:
                    pending_name = name
                    pending_award = ''
                continue

            # Some entries might not have Irish name
            if (re.match(r'^[A-Z]', line) and not line.startswith('ANALYSIS')
                and not line.startswith('ANAILÍS') and 'Category' not in line
                and len(line) > 3 and len(line) < 60 and not line.isdigit()
                and 'Centre' not in line and 'Mark' not in line and 'Award' not in line
                and 'Page' not in line and 'NATIONAL' not in line and 'REGIONAL' not in line
                and 'SPECIAL' not in line and 'SPONSORED' not in line):
                pending_name = line.strip()
                pending_award = ''

    doc.close()
    return results

# Process all booklets
all_results = []
booklet_dir = 'research/results-booklets'
years_files = {
    2019: '2019-results-booklet.pdf',
    2021: '2021-results-booklet.pdf',
    2022: '2022-results-booklet.pdf',
    2023: '2023-results-booklet.pdf',
    2024: '2024-results-booklet.pdf',
    2025: '2025-results-booklet.pdf',
}

for year, filename in years_files.items():
    filepath = os.path.join(booklet_dir, filename)
    if os.path.exists(filepath):
        try:
            results = extract_from_booklet(filepath, year)
            cat_b = [r for r in results if r['category'] == 'B']
            all_results.extend(results)
            print(f'{year}: Extracted {len(results)} total entries ({len(cat_b)} Category B)')
        except Exception as e:
            print(f'{year}: Error - {e}')

# Save ALL results (all categories)
with open('research/analysis/all_results_all_years.json', 'w', encoding='utf-8') as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)

cat_b = [r for r in all_results if r['category'] == 'B']
with open('research/analysis/category_b_all_years.json', 'w', encoding='utf-8') as f:
    json.dump(cat_b, f, indent=2, ensure_ascii=False)

print(f'\nTotal entries: {len(all_results)} (Category B: {len(cat_b)})')

# Find villages that appear in multiple years - track scores over time
from collections import defaultdict
village_history = defaultdict(list)
for entry in cat_b:
    key = f"{entry['village']}|{entry['county']}"
    village_history[key].append((entry['year'], entry['score'], entry.get('award', '')))

# Find biggest year-on-year jumps
print('\n=== BIGGEST YEAR-ON-YEAR SCORE JUMPS (Category B) ===')
print(f'{"Jump":>5} | {"Village":30s} | {"County":20s} | {"From":>15s} | {"To":>15s}')
print('-' * 95)
jumps = []
for key, scores in village_history.items():
    village, county = key.split('|')
    scores.sort(key=lambda x: x[0])
    for i in range(1, len(scores)):
        prev_year, prev_score, _ = scores[i-1]
        curr_year, curr_score, _ = scores[i]
        # Only consider consecutive or near-consecutive years
        jump = curr_score - prev_score
        jumps.append({
            'village': village, 'county': county,
            'from_year': prev_year, 'to_year': curr_year,
            'from_score': prev_score, 'to_score': curr_score,
            'jump': jump
        })

jumps.sort(key=lambda x: x['jump'], reverse=True)
for j in jumps[:30]:
    print(f"+{j['jump']:4d} | {j['village']:30s} | {j['county']:20s} | {j['from_year']}: {j['from_score']:3d} | {j['to_year']}: {j['to_score']:3d}")

# Tipperary North Cat B over time
print('\n=== TIPPERARY NORTH CAT B - ALL YEARS ===')
for entry in sorted(cat_b, key=lambda x: (x['year'], -x['score'])):
    if 'TIPPERARY NORTH' in entry['county']:
        award_str = f" [{entry['award']}]" if entry['award'] else ""
        print(f"{entry['year']} | {entry['village']:35s} | {entry['score']}{award_str}")

# Top 20 Cat B scores in 2025
print('\n=== TOP 20 CATEGORY B SCORES NATIONALLY - 2025 ===')
top_2025 = sorted([e for e in cat_b if e['year'] == 2025], key=lambda x: -x['score'])[:20]
for e in top_2025:
    award_str = f" [{e['award']}]" if e['award'] else ""
    print(f"{e['score']} | {e['village']:30s} | {e['county']}{award_str}")

# Save jumps data
with open('research/analysis/biggest_jumps.json', 'w', encoding='utf-8') as f:
    json.dump(jumps[:50], f, indent=2, ensure_ascii=False)
