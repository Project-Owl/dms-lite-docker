const express = require('express');
const asyncRoute = handler => (req, res, next) => Promise.resolve().then(() => handler(req,res)).catch(next);
function countValue(value, fallback = 100) {
  if (value === undefined) return fallback;
  if (typeof value !== 'string' || !/^\d+$/.test(value) || Number(value) < 1 || Number(value) > 1000) {
    const error = new Error('Count must be an integer from 1 to 1000'); error.status = 400; throw error;
  }
  return Number(value);
}
function addMessageRoutes(router, db) {
  router.get('/getAllData', asyncRoute(async (req,res) => res.json(await db.getAllData())));
  router.get('/getDataByDuckId/:duckId', asyncRoute(async (req,res) => res.json(await db.getDataByDuckId(req.params.duckId))));
  router.get('/getUniqueDucks', asyncRoute(async (req,res) => res.json(await db.getUniqueDucks())));
  router.get('/getLastCount/:count', asyncRoute(async (req,res) => res.json(await db.getLastCount(countValue(req.params.count)))));
}
function createDataRouter(db) {
  const router = express.Router();
  router.get('/', asyncRoute(async (req,res) => res.render('data',{something:await db.getAllData(),cookies:req.cookies})));
  addMessageRoutes(router,db);
  return router;
}
module.exports = {createDataRouter, addMessageRoutes, asyncRoute, countValue};
