const {test} = require('node:test');
const assert = require('node:assert/strict');
test('configuration requires credentials and validates capabilities and limits', () => {
  const {loadConfig} = require('../config');
  assert.throws(() => loadConfig({}), /MYSQL/);
  const env = {MYSQL_HOST:'mariadb',MYSQL_USER:'test',MYSQL_PASSWORD:'secret',MYSQL_DATABASE:'test'};
  const config = loadConfig(env);
  assert.equal(config.commandsEnabled,false);
  assert.equal(config.staleAfterSeconds,300);
  assert.equal(config.database.timezone,'Z');
  assert.equal(loadConfig({...env,COMMANDS_ENABLED:'true'}).commandsEnabled,true);
  assert.throws(() => loadConfig({...env,COMMANDS_ENABLED:'maybe'}));
  assert.throws(() => loadConfig({...env,DEVICE_STALE_SECONDS:'-1'}));
});
