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

    def __init__(self, host='hbase', timeout=60000000):
        self._conn_host = host
        self._timeout = timeout

    def tables(self):
        c = happybase.Connection(host=self._conn_host, timeout=self._timeout)
        try:
            return c.client.getTableNames()
        except Exception as e:
            print('Exception: {}, while trying to get a list of tables'.format(str(e)))
            return list()

    def create_table(self, table_name, family_name):
        if not bytes(table_name, encoding='utf-8') in self.tables():
            c = happybase.Connection(host=self._conn_host, timeout=self._timeout)
            try:
                c.create_table(table_name, {family_name: dict()})
            except Exception as e:
                print('Failed to create table: {}, trying once more'.format(table_name))
                c.create_table(table_name, {family_name: dict()})

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
            c = happybase.Connection(host=self._conn_host, timeout=self._timeout)
            return c.table(table_name)
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
        c = happybase.Connection(host=self._conn_host, timeout=self._timeout)

        c.delete_table(table_name, disable=True)
