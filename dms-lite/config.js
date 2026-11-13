function loadConfig(env = process.env) {
  for (const key of ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']) {
    if (!env[key]?.trim()) throw new Error(`${key} must be configured`);
  }
  const integer = (name, fallback, maximum) => {
    const value = env[name] ?? String(fallback);
    if (!/^\d+$/.test(value) || Number(value) < 1 || Number(value) > maximum) {
      throw new Error(`${name} must be an integer between 1 and ${maximum}`);
    }
    return Number(value);
  };
  const commands = env.COMMANDS_ENABLED ?? 'false';
  if (!['true', 'false'].includes(commands)) throw new Error('COMMANDS_ENABLED must be true or false');
  return {
    database: {host: env.MYSQL_HOST, user: env.MYSQL_USER, password: env.MYSQL_PASSWORD,
      database: env.MYSQL_DATABASE, connectionLimit: 5, connectTimeout: 5000,
      acquireTimeout: 10000, queryTimeout: 5000, timezone: 'Z', dateStrings: true},
    port: integer('PORT', 3000, 65535), commandsEnabled: commands === 'true',
    staleAfterSeconds: integer('DEVICE_STALE_SECONDS', 300, 31536000)
  };
}
module.exports = {loadConfig};
