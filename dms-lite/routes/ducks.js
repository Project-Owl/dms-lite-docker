const express = require('express');
const {addMessageRoutes, asyncRoute} = require('./data');
function createDucksRouter(db, {commandsEnabled, staleAfterSeconds}) {
  const router = express.Router();
  router.get('/', asyncRoute(async (req,res) => res.render('ducks', {
    something:await db.getDuckPlusData(), commandsEnabled, staleAfterSeconds, queued:req.query.queued === '1'
  })));
  addMessageRoutes(router,db);
  for (const [route,value] of [['postEnableWiFi','1'],['postDisableWiFi','0']]) {
    router.post('/'+route,asyncRoute(async(req,res)=>{
      const origin = req.get('origin');
      if (origin) {
        let allowed = false;
        try {const parsed = new URL(origin);allowed = ['http:','https:'].includes(parsed.protocol) && parsed.host === req.get('host');} catch {}
        if (!allowed) throw Object.assign(new Error('Cross-site commands are not allowed'),{status:403});
      }
      if (!commandsEnabled) throw Object.assign(new Error('Commands require a serial dispatcher'),{status:409});
      const duckId=req.body?.duck_id;
      if (typeof duckId !== 'string' || !duckId.trim() || duckId.length > 1024) {
        throw Object.assign(new Error('A valid device ID is required'),{status:400});
      }
      await db.postCommand(' /wifi/',value+duckId);
      res.redirect(303,'/ducks?queued=1');
    }));
  }
  return router;
}
module.exports = {createDucksRouter};
