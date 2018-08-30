import happybase


class HBaseAdapter(object):
    """
    Note: Need to increase timeout for thrift in hbase-site.xml
    <property>
        <name>hbase.thrift.server.socket.read.timeout</name>
        <value>6000000</value>
    </property>
    <property>
        <name>hbase.thrift.connection.max-idletime</name>
        <value>18000000</value>
    </property>
    """

    def __init__(self, host='hbase', connection_pool_size=10, timeout=6000000):
        self._conn_host = host
        self._conn_size = connection_pool_size
        self._timeout = timeout
        self._conn_pool = happybase.ConnectionPool(size=self._conn_size,
                                                   host=self._conn_host,
                                                   timeout=self._timeout)

        self._tables = {}

    def tables(self):
        with self._conn_pool.connection() as _conn:
            try:
                return _conn.client.getTableNames()
            except Exception as e:
                print('Exception: {}, while trying to get a list of tables'.format(str(e)))
                return _conn.client.getTableNames()

    def create_table(self, table_name, family_name):
        if not bytes(table_name, encoding='utf-8') in self.tables():
            with self._conn_pool.connection() as _conn:
                _conn.create_table(table_name, {family_name: dict()})

    def get_record(self, record_id, table_name, column_names, column_family):
        try:
            record = self.get_table(table_name).row(record_id)
            if record:
                result = {}
                for column_name in column_names:
                    fam_col = '{}:{}'.format(column_family, column_name).encode('utf-8')
                    result[column_name] = record.get(fam_col, '').decode('utf-8')
                return result
        except Exception as e:
            print('Exception: {}, while retrieving record: {}, from table: {}'.format(e, record_id, table_name))

        return None

    def get_table(self, table_name):
        try:
            if table_name not in self._tables:
                with self._conn_pool.connection() as _conn:
                    self._tables[table_name] = _conn.table(table_name)
            return self._tables[table_name]
        except Exception as e:
            print('Exception:{}, while retrieving table: {}'.format(e, table_name))
        return None

    def insert_record_value(self, record_id, value, table_name, column_family, column_name):
        table = self.get_table(table_name)
        if table:
            return table.put(record_id, {'{}:{}'.format(column_family, column_name): value})
        raise Exception('table: {} not found'.format(table_name))

    def insert_record(self, record_id, record, table_name):
        table = self.get_table(table_name)
        if table:
            return table.put(record_id, record)
        raise Exception('table: {} not found'.format(table_name))

    def insert_records_batch(self, records, table_name):
        """
        Adds records into hbase in batch mode
        :param records: list of records to be inserted, each record a tuple (id, data)
        :param table_name: table in hbase where records will be shipped to
        :return: exception in case of failure
        """
        table = self.get_table(table_name)
        batch = table.batch()
        for record in records:
            batch.put(record[0], record[1])
        batch.send()

    def delete_table(self, table_name):
        table_name = bytes(table_name, encoding='utf-8')
        with self._conn_pool.connection() as _conn:
            print(table_name)
            _conn.delete_table(table_name, disable=True)
