const mariadb = require('mariadb');

const pool = mariadb.createPool({
	host: "mariadb",
	user: process.env.MYSQL_USER,
	password: process.env.MYSQL_PASSWORD,
	database: process.env.MYSQL_DATABASE,
	connectionLimit: 5
});

// Test DB connection
testDbConnection();

// This will be updated
// CREATE TABLE clusterData(timestamp datetime, duck_id TEXT, message_id TEXT, payload TEXT, path TEXT);

async function testDbConnection() {
	let conn;
	try {
		conn = await pool.getConnection();
		const createTable = await conn.query("CREATE TABLE IF NOT EXISTS clusterData (timestamp DATETIME, duck_id TEXT, topic TEXT, message_id TEXT, payload TEXT, path TEXT, hops INT, duck_type INT)");
		console.log("Checked if table exists");
		const query = await conn.query("INSERT INTO clusterData(timestamp, duck_Id, topic, message_id, payload, path, hops, duck_type) values ('2021-11-14 00:00:00', 'asdf', 'asdf', 'asdf', 'asdf', 'asdf', 1, 1);");
	} catch (err) {
		throw err;
	} finally {
		if (conn) return conn.end();
	}
}

function getAllData() {
	const sql = "SELECT timestamp, duck_id, topic, message_id, payload, path, hops, duck_type  FROM clusterData ORDER BY timestamp DESC LIMIT 100;";

	return pool.query(sql).catch((error) => console.log(error));
}

function getDataByDuckId(duckId) {
	const sql = "SELECT timestamp, duck_id, topic, message_id, payload, path, hops, duck_type FROM clusterData WHERE duck_Id = ?;";

	return pool.query(sql, [[1, `${duckId}`]]).catch(error => console.log(error));
}

function getUniqueDucks() {
	const sql = "SELECT DISTINCT duck_id FROM clusterData;"

	return pool.query(sql).catch(error => console.log(error));
}

function getLastCount(count) {
	let sql = "SELECT timestamp, duck_id, topic, message_id, payload, path, hops, duck_type FROM clusterData ORDER BY timestamp DESC LIMIT ?;";

	return pool.query(sql, [[1, count]]).catch(error => console.log(error));
}

function getDuckPlusData() {
	const sql = `SELECT p.timestamp, p.duck_id, p.topic, p.message_id, p.payload, p.path, p.hops, p.duck_type  
		FROM 
		( 
			SELECT ROW_NUMBER() OVER ( PARTITION BY duck_id ORDER BY timestamp DESC ) 
				RowNum, timestamp, duck_id, topic, message_id, payload, path, hops, duck_type  
			FROM clusterData 
		) p
		WHERE p.RowNum = 1;`;

	return pool.query(sql).catch(error => console.log(error));
}

module.exports = { getAllData, getDataByDuckId, getUniqueDucks, getLastCount, getDuckPlusData };
