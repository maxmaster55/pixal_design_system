const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage();
p.on('pageerror',e=>console.log('err',e.message));
await p.goto('file://'+process.argv[2],{waitUntil:'networkidle'});
await p.evaluate(()=>document.fonts.ready);await p.waitForFunction(()=>document.documentElement.dataset.ready==="1");
await p.waitForTimeout(500);
await p.pdf({path:process.argv[3],preferCSSPageSize:true,printBackground:true});await b.close();})();
