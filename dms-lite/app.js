const express = require('express');
const path = require('node:path');
const fs = require('node:fs');
const {createHash} = require('node:crypto');
const {loadOverview,deviceState,formatUtc} = require('./routes/overview');
const cookieParser = require('cookie-parser');
const {createDataRouter, asyncRoute} = require('./routes/data');
const {createDucksRouter} = require('./routes/ducks');
const {createAnalyticsRouter} = require('./routes/analytics');
function createApp({db, commandsEnabled = false, staleAfterSeconds = 300}) {
  const app = express();
  app.disable('x-powered-by');
  app.set('views',path.join(__dirname,'views'));
  app.set('view engine','ejs');
  const stylesheet=path.join(__dirname,'public/stylesheets/app.css');
  app.locals.cssVersion=fs.existsSync(stylesheet)?createHash('sha256').update(fs.readFileSync(stylesheet)).digest('hex').slice(0,12):'build-required';
  Object.assign(app.locals,{commandsEnabled,staleAfterSeconds,deviceState,formatUtc});
  app.use((req,res,next)=>{
    const pages={'/':['overview','Overview'],'/data':['messages','Messages'],'/ducks':['ducks','Ducks'],'/settings':['settings','Settings'],'/setup':['setup','Setup guide']};
    const [activePage,pageTitle]=pages[req.path]||['','Workspace'];
    Object.assign(res.locals,{activePage,pageTitle,viewNow:Date.now(),retryPath:['/','/data','/ducks','/settings'].includes(req.path)?req.path:'/'});next();
  });
  app.use(express.json({limit:'64kb'}));
  app.use(express.urlencoded({extended:false,limit:'64kb'}));
  app.use(cookieParser());
  app.use(express.static(path.join(__dirname,'public')));
  app.use('/stylesheets/leaflet',express.static(path.join(__dirname,'node_modules/leaflet/dist')));
  app.get('/scripts/chart.js',(req,res) => res.sendFile(path.join(__dirname,'node_modules/chart.js/dist/chart.umd.min.js')));
  app.get('/health/live',(req,res) => res.json({status:'ok'}));
  app.get('/health/ready',asyncRoute(async (req,res) => {await db.checkReady(); res.json({status:'ready'});}));
  app.use('/api',createAnalyticsRouter(db));
  app.get('/',asyncRoute(async(req,res)=>res.render('index',{snapshot:await loadOverview(db,staleAfterSeconds,res.locals.viewNow)})));
  app.get('/setup',(req,res)=>res.render('setup'));
  app.use('/data',createDataRouter(db));
  app.use('/ducks',createDucksRouter(db,{commandsEnabled,staleAfterSeconds}));
  app.get('/settings',(req,res) => res.render('settings',{cookies:req.cookies}));
  app.use((req,res) => {
    if (req.path.startsWith('/api/') || req.path.startsWith('/health/')) return res.status(404).json({error:'Not found'});
    res.status(404).render('error',{message:'Page not found',error:{}});
  });
  app.use((error,req,res,next) => {
    const status = error.status >= 400 && error.status < 500 ? error.status : 503;
    const message = status < 500 ? error.message : 'Service unavailable. Please retry.';
    if (req.path.startsWith('/api/') || req.path.startsWith('/health/') || /\/get[A-Z]/.test(req.path)) {
      return res.status(status).json({error:message});
    }
    res.status(status).render('error',{message,error:{}});
  });
  return app;
}
module.exports = {createApp};
