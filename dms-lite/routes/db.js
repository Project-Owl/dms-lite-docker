const columns = ['timestamp', 'duck_id', 'topic', 'message_id', 'payload', 'path', 'hops', 'duck_type'];
const selected = columns.join(', ');
const incompatible = message => Object.assign(new Error(message),{code:'SCHEMA_INCOMPATIBLE'});
function textCapacity(type) {
  const capacity = {tinytext:255,text:65535,mediumtext:16777215,longtext:4294967295}[type];
  if (capacity) return capacity;
  const match = /^(?:var)?char\((\d+)\)$/.exec(type);
  return match ? Number(match[1]) : 0;
}
function validateColumns(table, metadata, required) {
  for (const field of required) {
    const column = metadata.find(item => item.Field === field);
    if (!column) throw incompatible(`Incompatible schema: ${table}.${field} column is missing`);
    const type = String(column.Type).toLowerCase();
    let valid;
    if (table === 'clusterData' && field === 'timestamp') valid = /^(?:datetime|timestamp)(?:\(\d\))?$/.test(type);
    else if (['hops','duck_type'].includes(field)) valid = /^(?:int|integer|bigint)(?:\(\d+\))?(?: unsigned)?(?: zerofill)?$/.test(type);
    else {
      const minimum = table === 'clusterData' ? 65535 : {timestamp:24,topic:7,payload:1025}[field];
      valid = textCapacity(type) >= minimum;
    }
    if (!valid) throw incompatible(`Incompatible schema: ${table}.${field} type or capacity cannot preserve packets`);
  }
  for (const column of metadata) {
    if (!required.includes(column.Field) && column.Null === 'NO' && column.Default == null && !/auto_increment|generated/i.test(column.Extra || '')) {
      throw incompatible(`Incompatible schema: ${table}.${column.Field} requires an insert value`);
    }
  }
}
function isoTimestamp(value) {
  if (value instanceof Date) return value.toISOString();
  const text = String(value).replace(' ', 'T');
  const date = new Date(/[zZ]$|[+-]\d\d:\d\d$/.test(text) ? text : text + 'Z');
  if (!Number.isFinite(date.getTime())) throw new Error('Invalid stored timestamp');
  return date.toISOString();
}
function createDatabase(pool) {
  const rows = async (sql, params = []) => (await pool.query(sql, params)).map(row => {
    const result = {...row};
    for (const [key,value] of Object.entries(result)) {
      if (typeof value === 'bigint') result[key] = value >= BigInt(Number.MIN_SAFE_INTEGER) && value <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(value) : value.toString();
    }
    if (row.timestamp != null) result.timestamp = isoTimestamp(row.timestamp);
    return result;
  });
  const recent = topic => rows('SELECT timestamp, duck_id, payload FROM clusterData WHERE topic = ? ORDER BY timestamp DESC LIMIT 1000', [topic]);
  const numeric = value => typeof value === 'string' && /^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(value.trim()) && Number.isFinite(Number(value));
  return {
    async initialize() {
      const conn = await pool.getConnection();
      try {
        await conn.query('CREATE TABLE IF NOT EXISTS clusterData (timestamp DATETIME, duck_id TEXT, topic TEXT, message_id TEXT, payload TEXT, path TEXT, hops INT, duck_type INT)');
        await conn.query('CREATE TABLE IF NOT EXISTS clusterCommands (timestamp TEXT, topic TEXT, payload TEXT)');
        for (const [table, required] of [['clusterData', columns], ['clusterCommands', ['timestamp','topic','payload']]]) {
          validateColumns(table,await conn.query(`SHOW COLUMNS FROM ${table}`),required);
        }
      } finally {conn.release();}
    },
    async checkReady() {
      await pool.query('SELECT timestamp, duck_id, topic, message_id, payload, path, hops, duck_type FROM clusterData LIMIT 0');
      await pool.query('SELECT timestamp, topic, payload FROM clusterCommands LIMIT 0');
    },
    getAllData: () => rows(`SELECT ${selected} FROM clusterData ORDER BY timestamp DESC LIMIT 100`),
    getDataByDuckId: duckId => rows(`SELECT ${selected} FROM clusterData WHERE duck_id = ? ORDER BY timestamp DESC LIMIT 1000`, [duckId]),
    getUniqueDucks: () => pool.query('SELECT DISTINCT duck_id FROM clusterData ORDER BY duck_id'),
    getLastCount: count => rows(`SELECT ${selected} FROM clusterData ORDER BY timestamp DESC LIMIT ?`, [count]),
    getDuckPlusData: () => rows(`SELECT ${selected} FROM (SELECT ROW_NUMBER() OVER (PARTITION BY duck_id ORDER BY timestamp DESC) AS row_num, ${selected} FROM clusterData) AS latest WHERE row_num = 1 ORDER BY duck_id`),
    async getTopics() {return (await pool.query('SELECT DISTINCT topic FROM clusterData ORDER BY topic')).map(row => row.topic);},
    async getReadings(topic, limit = 100) {
      return {samples:(await recent(topic)).filter(row => numeric(row.payload)).slice(0,limit).reverse()
        .map(row => ({timestamp:row.timestamp,value:Number(row.payload)}))};
    },
    async getAlert(topic,min,max) {
      const row = (await recent(topic)).find(row => numeric(row.payload) && (Number(row.payload) < min || Number(row.payload) > max));
      return {reading:row ? {timestamp:row.timestamp,duckId:row.duck_id,value:Number(row.payload)} : null};
    },
    async getLatestByDuckId(duckId) {
      const [row] = await rows('SELECT timestamp, topic, payload FROM clusterData WHERE duck_id = ? ORDER BY timestamp DESC LIMIT 1',[duckId]);
      return {reading:row ? {timestamp:row.timestamp,topic:row.topic,payload:row.payload} : null};
    },
    async postCommand(topic, payload) {
      await pool.query('INSERT INTO clusterCommands (timestamp, topic, payload) VALUES (?, ?, ?)', [new Date().toISOString(), topic, payload]);
    }
  };
}
module.exports = {createDatabase, isoTimestamp};
