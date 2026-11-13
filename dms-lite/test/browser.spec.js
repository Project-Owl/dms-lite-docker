const {test,expect}=require('@playwright/test');
test.beforeEach(async({request,context})=>{
  // Exercise a cold cache with internet destinations blocked on every page.
  await context.route('**/*',route=>{
    const url=new URL(route.request().url());
    return url.hostname==='127.0.0.1'&&['3107','3108'].includes(url.port)?route.continue():route.abort();
  });
  await request.get('/__fixture?populated');
});
test('new browser renders charts and inert device text without Flask or remote assets',async({page})=>{
  const errors=[],failed=[],remote=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('response',response=>{if(response.status()>=400)failed.push(response.url());});
  page.on('request',request=>{if(!request.url().startsWith('http://127.0.0.1:3107/'))remote.push(request.url());});
  await page.goto('/data');
  await expect(page.locator('#chart-status')).toContainText('1');
  await expect(page.locator('#info-body')).toContainText('<img');
  expect(await page.evaluate(()=>window.PACKET_EXECUTED)).toBeUndefined();
  expect(await page.locator('.gmaps-button').count()).toBe(0);
  expect(await page.locator('meta[name=viewport]').getAttribute('content')).not.toContain('user-scalable=no');
  await page.goto('/ducks');await expect(page.getByRole('button',{name:'WiFi ON'})).toHaveCount(0);
  for(const path of ['/settings','/setup','/']){
    await page.goto(path);
    await expect(page.getByRole('main')).toBeVisible();
    await expect(page.getByText('Powered by Clusterduck Protocol',{exact:false})).toBeVisible();
  }
  expect(errors).toEqual([]);expect(failed).toEqual([]);expect(remote).toEqual([]);
});
test('settings migrate broken storage, persist choices and render network text safely',async({page})=>{
  await page.addInitScript(()=>{if(!sessionStorage.getItem('seeded')){localStorage.setItem('dmsLite.preferences','{');sessionStorage.setItem('seeded','1');}});
  await page.goto('/settings');
  await expect(page.locator('#firsttopic')).toContainText('sensor/temp');
  await page.locator('#firsttopic').selectOption('sensor/temp');
  await page.locator('#datamount').fill('12');await page.locator('#toData').click();
  await expect(page.locator('#settings-status')).toContainText('Saved');
  await page.locator('#min_alert').fill('-2.5');await page.locator('#max_alert').fill('10');await page.locator('#alert_bt').click();
  await expect(page.locator('#settings-status')).toContainText('Saved');
  await page.goto('/data');await expect(page.locator('#chart-status')).toContainText('1');
  await expect(page.locator('#alert-body')).toContainText('<img');
  expect(await page.evaluate(()=>window.PACKET_EXECUTED)).toBeUndefined();
});
test('empty database and failed chart panel leave usable independent panels',async({page,request})=>{
  await request.get('/__fixture?empty');await page.goto('/data');
  await expect(page.locator('#chart-status')).toContainText('No');
  await request.get('/__fixture?populated');
  await page.route('**/api/topics',route=>route.fulfill({status:503,contentType:'application/json',body:'{"error":"unavailable"}'}));
  await page.reload();await expect(page.locator('#chart-status').getByRole('button',{name:'Retry',exact:true})).toBeVisible();
  await expect(page.locator('#info-body')).toContainText('sensor/temp');
});
test('dark overview uses real snapshots and a local setup path',async({page,request},testInfo)=>{
 await page.goto('/');
 await expect(page.getByRole('heading',{name:'Overview',exact:true})).toBeVisible();
 await expect(page.locator('[data-metric=messages]')).toHaveText('2');
 await expect(page.locator('[data-metric=devices]')).toHaveText('1');
 expect(await page.locator('body').evaluate(el=>getComputedStyle(el).backgroundColor)).toBe('rgb(0, 0, 0)');
 await expect(page.getByRole('combobox',{name:'Theme'})).toHaveCount(0);
 await expect(page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Overview'})).toHaveAttribute('aria-current','page');
 expect(await page.locator('link[rel=stylesheet]').first().getAttribute('href')).toMatch(/app\.css\?v=[a-f0-9]+/);
 await page.screenshot({path:`../.scratch/modernization/frontend-${testInfo.project.name}.png`,fullPage:true});
 await request.get('/__fixture?empty');await page.reload();
 await expect(page.getByRole('heading',{name:'No messages yet',exact:true})).toBeVisible();
 await expect(page.getByRole('main')).toContainText('MQTT or USB serial');
 await expect(page.getByRole('main')).toContainText('matching DMS Lite firmware');
 await page.screenshot({path:`../.scratch/modernization/empty-${testInfo.project.name}.png`,fullPage:true});
 await page.getByRole('main').getByRole('link',{name:'Setup guide',exact:true}).click();await expect(page.getByRole('heading',{name:'Setup guide',exact:true})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
test('message filters preserve raw text and long identifiers fit a narrow viewport',async({page,request})=>{
 await request.get('/__fixture?long');await page.goto('/data');
 await expect(page.getByRole('searchbox',{name:'Search messages'})).toBeVisible();
 await page.getByRole('searchbox',{name:'Search messages'}).fill('no-such-payload');
 await expect(page.locator('#message-filter-status')).toContainText('0');
 await page.getByRole('searchbox',{name:'Search messages'}).fill('');
 await page.getByRole('combobox',{name:'Filter by topic'}).selectOption('gps');
 await expect(page.locator('#message-filter-status')).toContainText('1');
 expect(await page.evaluate(()=>window.PACKET_EXECUTED)).toBeUndefined();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.goto('/ducks');expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.getByText('Message details',{exact:true}).first().click();await expect(page.locator('details[open]')).toHaveCount(1);
});
test('overview keeps device results when messages are unavailable',async({page,request})=>{
 await request.get('/__fixture?unavailable');await page.goto('/');
 await expect(page.locator('[data-metric=messages]')).toHaveText('—');
 await expect(page.locator('[data-metric=devices]')).toHaveText('1');
 await expect(page.getByText('Could not load messages.',{exact:true})).toBeVisible();
 await expect(page.getByRole('heading',{name:'No messages yet',exact:true})).toHaveCount(0);
});
test('serial command forms remain gated and describe queued delivery',async({page})=>{
 await page.goto('http://127.0.0.1:3108/ducks');
 await expect(page.getByRole('button',{name:'WiFi ON'})).toHaveCount(1);
 await expect(page.getByText('Queued commands do not confirm device receipt.',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'WiFi ON'}).click();await expect(page.getByRole('status')).toContainText('Command queued');
});
for(const staleFailure of [false,true])test(`new chart selection ignores older ${staleFailure?'failure':'success'}`,async({page})=>{
 let release;const gate=new Promise(resolve=>{release=resolve;});let held=false;
 await page.addInitScript(()=>localStorage.removeItem('dmsLite.preferences'));
 await page.route('**/api/readings?*',async route=>{
  const topic=new URL(route.request().url()).searchParams.get('topic');
  if(topic==='sensor/temp'&&!held){held=true;await gate;await route.fulfill({status:staleFailure?503:200,contentType:'application/json',body:staleFailure?'{}':JSON.stringify({samples:[{timestamp:'2026-10-28T12:00:00Z',value:2.5}]})});}
  else await route.fulfill({contentType:'application/json',body:JSON.stringify({samples:[{timestamp:'2026-10-28T12:00:00Z',value:7}]})});
 });
 try{
  await page.goto('/data');await expect.poll(()=>held).toBe(true);
  await page.locator('#chart-topic').selectOption('humidity');
  await expect.poll(()=>page.evaluate(()=>Chart.getChart(document.getElementById('mychart'))?.data.datasets[0]?.label)).toBe('humidity');
  const response=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/readings'&&new URL(r.url()).searchParams.get('topic')==='sensor/temp');release();await (await response).finished();
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  expect(await page.evaluate(()=>Chart.getChart(document.getElementById('mychart')).data.datasets[0].label)).toBe('humidity');
  await expect(page.locator('#chart-status').getByRole('button',{name:'Retry',exact:true})).toHaveCount(0);
 }finally{release();}
});
for(const pending of [true,false])test(`settings preserve unavailable selections during ${pending?'pending requests':'partial failure'}`,async({page})=>{
 const saved={version:1,chartType:'line',topic:'sensor/temp',secondTopic:'humidity',duckId:'SAVED-DUCK',limit:100,alerts:[]};
 await page.addInitScript(value=>localStorage.setItem('dmsLite.preferences',JSON.stringify(value)),saved);
 let release;const gate=new Promise(resolve=>{release=resolve;});
 await page.route('**/api/ducks',async route=>{if(pending)await gate;await route.fulfill({status:503,contentType:'application/json',body:'{}'});});
 if(pending)await page.route('**/api/topics',async route=>{await gate;await route.continue();});
 try{
  await page.goto('/settings');
  if(!pending)await expect(page.getByRole('button',{name:'Retry',exact:true})).toBeVisible();
  await page.locator('#graphtype').selectOption('bar');await page.locator('#toData').click();
  const actual=await page.evaluate(()=>JSON.parse(localStorage.getItem('dmsLite.preferences')));
  expect(actual).toMatchObject({...saved,chartType:'bar'});
  if(!pending)await expect(page.getByRole('button',{name:'Retry',exact:true})).toBeVisible();
 }finally{release();}
});

test('essential monospace data uses at least 13px text',async({page})=>{
 await page.goto('/data');
 const sizes=await page.locator('.message-table .mono,.message-table .topic-tag').evaluateAll(elements=>elements.map(el=>parseFloat(getComputedStyle(el).fontSize)));
 expect(sizes.length).toBeGreaterThan(0);
 expect(Math.min(...sizes)).toBeGreaterThanOrEqual(13);
});
