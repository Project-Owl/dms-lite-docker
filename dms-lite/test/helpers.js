const {createServer} = require('node:http');
exports.serve = async function (t, app) {
  const server = createServer(app);
  await new Promise((resolve, reject) => {server.once('error',reject); server.listen(0,'127.0.0.1',resolve);});
  t.after(() => new Promise(resolve => {server.close(resolve); server.closeAllConnections();}));
  return `http://127.0.0.1:${server.address().port}`;
};
exports.emptyDb = () => ({
  checkReady: async () => {}, getAllData: async () => [], getDuckPlusData: async () => [],
  getDataByDuckId: async () => [], getUniqueDucks: async () => [], getLastCount: async () => [],
});
