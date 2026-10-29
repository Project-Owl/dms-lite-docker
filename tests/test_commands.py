import json
import unittest
from test_ingestion import adapters

class CommandConnection:
    def __init__(self,rows): self.rows=rows; self.closed=False; self.rolled_back=False; self.committed=False; self.statements=[]
    def cursor(self): return self
    def execute(self,sql,values=()):
        self.statements.append((sql,values))
        if sql.startswith('DELETE'):
            assert 'LIMIT 1' in sql
            assert 'timestamp=? AND topic=? AND payload=?' in sql
            self.rows.remove(tuple(values))
    def fetchone(self): return self.rows[0] if self.rows else None
    def commit(self): self.committed=True
    def rollback(self): self.rolled_back=True
    def close(self): self.closed=True

class CommandsTests(unittest.TestCase):
    def test_empty_queue_closes_connection(self):
        conn=CommandConnection([])
        self.assertFalse(adapters()[0].dispatch_one(lambda:conn,None))
        self.assertTrue(conn.closed)

    def test_success_writes_current_wire_format_and_removes_only_matching_row(self):
        rows=[('same-time',' /wifi/','1DUCK'),('same-time','other','keep')]
        conn=CommandConnection(rows); writes=[]
        class Port:
            def write(self,raw): writes.append(raw); return len(raw)
        self.assertTrue(adapters()[0].dispatch_one(lambda:conn,Port()))
        self.assertEqual(json.loads(writes[0]),{'topic':' /wifi/','payload':'1DUCK'})
        self.assertFalse(writes[0].endswith(b'\n'))
        self.assertEqual(rows,[('same-time','other','keep')])
        self.assertTrue(conn.committed and conn.closed)
        self.assertTrue(any('ORDER BY timestamp' in sql and 'FOR UPDATE' in sql for sql,_ in conn.statements))

    def test_partial_and_failed_writes_keep_the_command(self):
        for result in [1,OSError('disconnected')]:
            rows=[('time',' /wifi/','1DUCK')]; conn=CommandConnection(rows)
            class Port:
                def write(self,raw):
                    if isinstance(result,Exception): raise result
                    return result
            self.assertFalse(adapters()[0].dispatch_one(lambda:conn,Port()))
            self.assertEqual(len(rows),1)
            self.assertTrue(conn.rolled_back and conn.closed)

if __name__=='__main__': unittest.main()
