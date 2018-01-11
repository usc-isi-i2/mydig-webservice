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
                config['rss_feed_crawler']['kafka_topic'],
                bootstrap_servers=config['kafka']['servers'],
                group_id=config['rss_feed_crawler']['group_id'],
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                auto_offset_reset='earliest'
            )

            print 'rss consumer started'

            for msg in consumer:
                # print msg.value.keys()
                # print msg.value['project_name']
                try:
                    data = msg.value
                    url = config['rss_feed_crawler']['upload']['endpoint'].format(project_name=data['project_name'])
                    # url = config['ache']['upload']['endpoint'].format(project_name='ache')
                    # del data['project']
                    payload = {
                        'file_name': config['rss_feed_crawler']['upload']['file_name'],
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
