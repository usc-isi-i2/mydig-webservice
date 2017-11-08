import os
import json
import sys
import codecs
import time

import requests
from kafka import KafkaProducer, KafkaConsumer

sys.path.append(os.path.join('../ws'))
from config import config

if __name__ == '__main__':

    while True:
        try:
            consumer = KafkaConsumer(
                'ache',
                bootstrap_servers=config['kafka']['servers'],
                group_id=config['ache']['group_id'],
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                auto_offset_reset='earliest'
            )
            consumer.subscribe(config['ache']['kafka_topic'])

            print 'consumer started'

            for msg in consumer:
                try:
                    data = msg.value
                    # url = config['ache']['upload']['endpoint'].format(project_name=data['project'])
                    url = config['ache']['upload']['endpoint'].format(project_name='ache')
                    # del data['project']
                    payload = {
                        'file_name': config['ache']['upload']['file_name'],
                        'file_type': 'json_lines'
                    }
                    files = {
                        'file_data': ('', json.dumps(data), 'application/octet-stream')
                    }
                    # print url, payload
                    resp = requests.post(url, data=payload, files=files, timeout=10)

                except Exception as e:
                    print e

        except Exception as e:
            print e
            time.sleep(5)



# bin/kafka-topics.sh --zookeeper zookeeper:2181 --list
# bin/kafka-console-producer.sh --broker-list kafka:9092 --topic ache
# bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic ache --from-beginning
# {"url": "testache.org", "doc_id":"0001", "project":"test_ache", "raw_content":"<html>test</html>"}
