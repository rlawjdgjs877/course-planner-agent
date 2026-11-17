from pathlib import Path
import json,re,html,shutil,collections
base=Path(__file__).resolve().parents[1]
config=[('platform','플솦','플솦','전공'),('computing','컴학','컴학 공통','전공'),('research','첨컴','첨컴','전공'),('core-natural','첨성인핵심자연','첨성인핵심 · 자연','교양'),('core-humanities','첨성인핵심인문','첨성인핵심 · 인문','교양'),('literacy','첨성인소양','첨성인소양','교양'),('foundation','첨성인기초','첨성인기초','교양'),('ai','인컴','인컴','전공'),('advanced','심컴 과목','심컴','전공'),('global','글솝','글솦','전공')]
fields=['crseNo','sbjetCd','sbjetNm','sbjetDvnno','estblYear','estblSmstrSctnm','estblGrade','estblUnivNm','estblDprtnNm','sbjetSctnm','crdit','thryTime','prctsTime','totalPrfssNm','lssnsTimeInfo','lssnsRealTimeInfo','lctrmInfo','rmnmCd','rmrk','appcrCnt','attlcPrscpCnt','pckgeRqstCnt']
def clean(v):
 if v is None:return ''
 return html.unescape(re.sub(r'<[^>]*>',' ',str(v))).strip()
def norm(v):return re.sub(r'\s+','',v)
source_dir=base/'data/course-sources';source_dir.mkdir(parents=True,exist_ok=True)
merged={};sources=[];bycode=collections.defaultdict(list)
for sourceid,filename,label,group in config:
 local=source_dir/(sourceid+'.json')
 if not local.exists():shutil.copyfile(Path('C:/Users/조현택/Downloads')/(filename+'.json'),local)
 d=json.loads(local.read_text(encoding='utf-8-sig'));rows=d['data']
 assert d['success'] and d['statusCode']==200
 sources.append(dict(id=sourceid,label=label,group=group,filename=filename+'.json',timestamp=d.get('timestamp'),count=len(rows)))
 for row in rows:
  assert row['crseNo'] and row['sbjetCd'] and row['sbjetNm']
  record={k:(row.get(k) if k in ['appcrCnt','attlcPrscpCnt','pckgeRqstCnt'] else clean(row.get(k))) for k in fields}
  record['sourceId']=sourceid
  key='|'.join([record['estblYear'],clean(row.get('estblSmstrSctcd')) or record['estblSmstrSctnm'],record['crseNo']])
  if key not in merged:merged[key]=dict(id=key,records=[])
  merged[key]['records'].append(record)
  bycode[record['sbjetCd']].append(record)
# Keep stable IDs for the 66 existing PDF courses so saved checks survive.
p=base/'app/lib/courses.ts';s=p.read_text(encoding='utf-8-sig')
start=s.index('[',s.index('=',s.index('export const courses:')))
existing=json.loads(s[start:].strip().removesuffix(';'))
# Use the original PDF entries only on subsequent runs.
existing=[c for c in existing if c['id'].startswith('knu-')]
for c in existing:
 c.update(year=0,years=[],credits=None,semester='개설 정보 미확인',category='문서 수록 과목',sourceIds=[],creditOptions=[])
 c.pop('code',None)
matched=set()
for code,records in sorted(bycode.items()):
 name=records[0]['sbjetNm'];assert len({norm(r['sbjetNm']) for r in records})==1
 course=next((c for c in existing if norm(c['name'])==norm(name)),None)
 if course is None:
  course=dict(id='course-'+code,name=name);existing.append(course)
 years=sorted({int(r['estblGrade']) for r in records if r['estblGrade'] in ['1','2','3','4']})
 allgrades=any(r['estblGrade']=='*' for r in records)
 credits=sorted({float(r['crdit']) for r in records if r['crdit'] and re.fullmatch(r'\d+(\.\d+)?',r['crdit'])})
 categories=sorted({r['sbjetSctnm'] for r in records if r['sbjetSctnm']})
 course.update(code=code,year=years[0] if len(years)==1 and not allgrades else 0,years=years,allGrades=allgrades,credits=credits[0] if len(credits)==1 else None,creditOptions=credits,semester='2026년 2학기',category=' / '.join(categories),sourceIds=sorted({r['sourceId'] for r in records}))
 matched.add(code)
type_text='export type Course = { id: string; name: string; year: number; years?: number[]; allGrades?: boolean; category: string; credits: number | null; creditOptions?: number[]; semester: string; sourceIds?: string[]; code?: string };\n'
p.write_text(type_text+'export const courses: Course[] = '+json.dumps(existing,ensure_ascii=False,indent=2)+';\n',encoding='utf-8')
output=base/'app/lib/data';output.mkdir(parents=True,exist_ok=True)
(output/'offerings.json').write_text(json.dumps(list(merged.values()),ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(output/'sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
report=dict(sourceCount=len(sources),sourceRows=sum(s['count'] for s in sources),offeringCount=len(merged),courseCodes=len(matched),catalogCourses=len(existing),missingTime=sum(not any(r['lssnsRealTimeInfo'] for r in x['records']) for x in merged.values()))
(output/'import-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
