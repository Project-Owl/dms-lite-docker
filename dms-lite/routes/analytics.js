const express = require('express');
const {asyncRoute,countValue} = require('./data');
function badRequest(message) {return Object.assign(new Error(message),{status:400});}
function topicValue(value) {
  if (typeof value !== 'string' || !value.trim() || value.length > 1024) throw badRequest('A topic is required (maximum 1024 characters)');
  return value;
}
function numberValue(value) {
  if (typeof value !== 'string' || !/^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(value.trim()) || !Number.isFinite(Number(value))) {
    throw badRequest('Thresholds must be finite numbers');
  }
  return Number(value);
}
function createAnalyticsRouter(db) {
  const router = express.Router();
  router.get('/topics',asyncRoute(async(req,res)=>res.json(await db.getTopics())));
  router.get('/ducks',asyncRoute(async(req,res)=>res.json((await db.getUniqueDucks()).map(row=>row.duck_id))));
  router.get('/readings',asyncRoute(async(req,res)=>res.json(await db.getReadings(topicValue(req.query.topic),countValue(req.query.limit)))));
  router.get('/alerts',asyncRoute(async(req,res)=>{
    const topic=topicValue(req.query.topic), min=numberValue(req.query.min), max=numberValue(req.query.max);
    if (min > max) throw badRequest('Minimum must not exceed maximum');
    res.json(await db.getAlert(topic,min,max));
  }));
  router.get('/ducks/:duckId/latest',asyncRoute(async(req,res)=>res.json(await db.getLatestByDuckId(req.params.duckId))));
  return router;
}
module.exports = {createAnalyticsRouter};
