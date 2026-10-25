const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();
for(const f of (process.argv[2]||'1920x1080,1600x1000,1440x1080,1080x1440').split(',')){
 const [w,h]=f.split('x').map(Number);
 const p=await b.newPage({viewport:{width:w,height:h},deviceScaleFactor:1});
 await p.goto('file://'+__dirname+'/cover.html?f='+f);
 await p.waitForSelector('body[data-ready]');await p.waitForTimeout(300);
 await (await p.$('#c')).screenshot({path:`../EP05封面_${f}.png`});await p.close();}
await b.close();})();
