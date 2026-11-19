"""Headless UI integration test using mocked school API only; never logs in to a school account."""
from pathlib import Path
import base64,json,re,sys
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1]
url=sys.argv[1] if len(sys.argv)>1 else 'http://localhost:3105'
s=(root/'app/lib/courses.ts').read_text(encoding='utf-8-sig');a=s.index('[',s.index('=',s.index('export const courses:')))
catalog=json.loads(s[a:].strip().removesuffix(';'));known=next(c for c in catalog if c.get('code'))
state={'available':True,'finished':False,'starts':0,'stops':0,'actions':[]}
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True)
 context=browser.new_context(viewport={'width':1280,'height':900})
 fixture=context.new_page();fixture.set_viewport_size({'width':1280,'height':800})
 fixture.set_content('<html><body style="font:24px sans-serif;background:#edf4ff;padding:70px"><h1>Mock school screen</h1><p>Test fixture only. No real account.</p><div style="background:white;border:1px solid #aab;padding:30px;width:400px">Mock input field</div></body></html>')
 jpeg=base64.b64encode(fixture.screenshot(type='jpeg')).decode();fixture.close()
 headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET, POST, OPTIONS','Access-Control-Allow-Headers':'Content-Type, X-Import-Session','Content-Type':'application/json'}
 def mock(route):
  request=route.request
  if request.method=='OPTIONS':route.fulfill(status=204,headers=headers);return
  action=request.url.rsplit('/',1)[-1]
  if action=='status':data={'enabled':True,'installed':True,'available':state['available'],'reason':None if state['available'] else '미사용 테스트 상태','idle_minutes':10}
  elif action=='start':state['starts']+=1;data={'session':'mock-private-session-not-for-storage'}
  elif action=='input':state['actions'].append(request.post_data_json);data={'ok':True}
  elif action=='stop':state['stops']+=1;data={'ok':True,'closed':True}
  elif action=='navigate':data={'ok':True}
  elif action=='frame':data={'image':jpeg if not state['finished'] else None,'frame_id':'mock-frame','status':'모의 학교 화면','finished':state['finished'],'courses':[{'code':known['code'],'name':known['name'],'credits':3,'category':'전공','grade':'A+','password':'should-not-be-stored'},{'code':'TEST9999','name':'모의 과거 과목','credits':2,'category':'교양'}] if state['finished'] else [],'duplicates':[],'expires_in':600}
  else:route.fulfill(status=404,headers=headers,body='{}');return
  route.fulfill(status=200,headers=headers,body=json.dumps(data))
 context.route('**/import/knu/*',mock)
 page=context.new_page();page.goto(url,wait_until='networkidle')
 school=page.get_by_role('button',name='학교 로그인으로 시작',exact=True);manual=page.get_by_role('button',name='직접 입력하기',exact=True)
 expect(school).to_be_enabled();left=school.bounding_box();right=manual.bounding_box();assert abs(left['y']-right['y'])<1 and abs(left['height']-right['height'])<1
 school.click();start=page.get_by_role('button',name='학교 로그인 화면 열기',exact=True);expect(start).to_be_disabled()
 page.get_by_role('checkbox',name=re.compile('안내를 확인했으며')).check();expect(start).to_be_enabled();start.click()
 expect(page.get_by_alt_text('학교 시스템 원격 화면')).to_be_visible()
 page.locator('.knu-remote-screen').click(position={'x':100,'y':80})
 field=page.get_by_label('학교 화면의 선택한 입력칸으로 글자 보내기');field.fill('dummy-input-test-only')
 with page.expect_response('**/import/knu/input'):page.get_by_role('button',name='전송 후 지우기').click()
 expect(field).to_have_value('');assert any(a.get('text')=='dummy-input-test-only' for a in state['actions'])
 assert 'mock-private-session-not-for-storage' not in page.evaluate('JSON.stringify(localStorage)')
 (root/'tmp').mkdir(exist_ok=True);page.locator('.school-import-panel').screenshot(path=str(root/'tmp/school-import-panel.png'))
 state['finished']=True
 expect(page.get_by_role('heading',name='읽어 온 이수 과목 2개',exact=True)).to_be_visible(timeout=10000)
 expect(page.get_by_alt_text('학교 시스템 원격 화면')).to_have_count(0)
 page.get_by_role('button',name='확인한 이수 과목 반영',exact=True).click()
 page.wait_for_function("JSON.parse(localStorage.getItem('campus-finder-knu-documents-v2')).importedCourses.length === 2")
 stored=page.evaluate("JSON.parse(localStorage.getItem('campus-finder-knu-documents-v2'))")
 assert known['id'] in stored['selected'];assert len(stored['importedCourses'])==2
 assert 'should-not-be-stored' not in json.dumps(stored) and 'mock-private-session-not-for-storage' not in json.dumps(stored)
 assert all(set(course)=={'code','name','credits','category'} for course in stored['importedCourses'])
 assert state['stops']>=1
 page.get_by_text('불러온 과목 확인·제외',exact=True).click()
 row=page.locator('.imported-history-summary .imported-courses-table>div').filter(has=page.get_by_text(known['code'],exact=True))
 row.get_by_role('button',name='이수 내역에서 제외',exact=True).click()
 page.wait_for_function("JSON.parse(localStorage.getItem('campus-finder-knu-documents-v2')).importedCourses.length === 1")
 stored=page.evaluate("JSON.parse(localStorage.getItem('campus-finder-knu-documents-v2'))");assert known['id'] not in stored['selected']
 state['finished']=False;start.click();expect(page.get_by_alt_text('학교 시스템 원격 화면')).to_be_visible()
 with page.expect_response('**/import/knu/stop'):page.locator('.sidebar').get_by_role('button',name='시간표 조건 설정',exact=True).click()
 assert state['stops']>=2
 state['available']=False;page.reload(wait_until='networkidle');page.get_by_role('button',name='학교 로그인으로 시작',exact=True).click()
 expect(page.get_by_text('미사용 테스트 상태',exact=True)).to_be_visible();expect(page.get_by_role('button',name='학교 로그인 화면 열기',exact=True)).to_be_disabled()
 page.get_by_role('button',name='입력 방법 바꾸기',exact=True).click();page.get_by_role('button',name='직접 입력하기',exact=True).click()
 expect(page.get_by_role('heading',name='나의 컴학 생활',exact=True)).to_be_visible()
 context.close();browser.close()
print('PASS: aligned welcome actions, explicit consent, mock remote input + immediate clearing, no token/credential persistence, exact-code application, historical course retention, removal sync, session cleanup on navigation and unavailable-service fallback. No real school account was used.')
