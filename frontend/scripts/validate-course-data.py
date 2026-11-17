from pathlib import Path
import json,re,collections
root=Path(__file__).resolve().parents[1]
read=lambda name:json.loads((root/'app/lib/data'/name).read_text(encoding='utf-8'))
sources=read('sources.json');offerings=read('offerings.json');report=read('import-report.json')
assert len(sources)==10 and report['sourceRows']==816 and len(offerings)==781
assert len({o['id'] for o in offerings})==len(offerings)
assert sum(len(o['records']) for o in offerings)==816
assert len({r['sbjetCd'] for o in offerings for r in o['records']})==254
for source in sources:
 raw=json.loads((root/'data/course-sources'/(source['id']+'.json')).read_text(encoding='utf-8-sig'))
 imported=[r for o in offerings for r in o['records'] if r['sourceId']==source['id']]
 assert len(imported)==source['count']==len(raw['data'])
 assert collections.Counter(r['crseNo'] for r in imported)==collections.Counter(r['crseNo'] for r in raw['data'])
 assert collections.Counter(r['sbjetCd'] for r in imported)==collections.Counter(r['sbjetCd'] for r in raw['data'])
for offering in offerings:
 assert len({r['sourceId'] for r in offering['records']})==len(offering['records']),offering['id']
 assert all('<br' not in r['rmrk'].lower() and '<b>' not in r['rmrk'].lower() for r in offering['records'])
# Same section, different majors: both grade values must survive merging.
nlp=next(o for o in offerings if o['records'][0]['crseNo']=='CAIB0211-001')
assert {r['estblGrade'] for r in nlp['records']} >= {'3','4'}
assert any('토' in r['lssnsRealTimeInfo'] for o in offerings for r in o['records'])
assert sum(not any(r['lssnsRealTimeInfo'] for r in o['records']) for o in offerings)==2
s=(root/'app/lib/courses.ts').read_text(encoding='utf-8-sig');start=s.index('[',s.index('=',s.index('export const courses:')))
courses=json.loads(s[start:].strip().removesuffix(';'))
assert len(courses)==288 and len({c['id'] for c in courses})==288
assert len([c for c in courses if c['id'].startswith('knu-')])==66
assert {c['code'] for c in courses if 'code' in c}=={r['sbjetCd'] for o in offerings for r in o['records']}
print('PASS: all 10 sources / 816 rows retained; 781 unique sections; 254 codes; 288 catalog entries; 66 saved course IDs preserved; differing major grades, weekends and 2 unknown-time sections retained.')
