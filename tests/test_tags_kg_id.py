from ws import ws
import unittest
import json


class FlaskrTestCase(unittest.TestCase):
    def setUp(self):
        ws.app.config['TESTING'] = True
        self.app = ws.app.test_client()

    def test_hello(self):
        response = self.app.get('/')
        self.assertEquals(200, response.status_code)

    def test_create_project(self):
        pass
        # req_data = dict({'project_name': 'test_project_1'})
        # req_data['sources'] = [{"type": "cdr", "url": "http://...", "index_name": "name of the index",
        #                         "elastic_search_doctype": "the type in elastic search", "elastic_search_query": {},
        #                         "start_date": "date-in-iso-format-at-any-resolution",
        #                         "end_date": "date-in-iso-format-at-any-resolution"}]
        # response = self.app.post('/projects', data=json.dumps(req_data))
        # print 'create'
        # print response

    def test_add_tag_entity(self):
        req_data = dict({'project_name': 'dig3-ht'})
        req_data['sources'] = [{"type": "cdr", "url": "http://...", "index_name": "name of the index",
                                "elastic_search_doctype": "the type in elastic search", "elastic_search_query": {},
                                "start_date": "date-in-iso-format-at-any-resolution",
                                "end_date": "date-in-iso-format-at-any-resolution"}]
        print json.dumps(req_data)
        response = self.app.post('/projects', data=json.dumps(req_data))
        req_data = dict()
        req_data['human_annotation'] = 0
        req_data['tags'] = 'test-tag'
        response = self.app.post("/projects/dig3-ht/entities/092F55350A6125D8550D7652F867EBB9EB027C8EADA2CC1BAC0BEB1F48FE6D2B/tags", data=json.dumps(req_data))
        req_data['human_annotation'] = 1
        print json.dumps(req_data)
        response = self.app.post(
            "/projects/dig3-ht/entities/CAFAE7C3F6B4A45A6ADB342A8C09051E34DDE45D4ECD7A9620BDFFCE55702C58/tags",
            data=json.dumps(req_data))
        print response

if __name__ == '__main__':
    unittest.main()