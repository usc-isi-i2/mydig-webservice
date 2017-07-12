import requests
from pywebhdfs.webhdfs import PyWebHdfsClient


class HdfsOp(object):
    def __init__(self, web_hdfs_url='http://10.1.94.54:14000/webhdfs/v1'):
        self.web_hdfs_url = web_hdfs_url

    def create_dir(self, path, hdfs_user='worker'):
        url = '{}{}/?op=MKDIRS&user.name={}'.format(self.web_hdfs_url, path, hdfs_user)
        return requests.put(url)

    def create_or_overwrite_file(self, path, f, hdfs_user='worker', request_extra_opts={}):
        hdfs = PyWebHdfsClient(host='10.1.94.54', port=14000, user_name=hdfs_user, request_extra_opts=request_extra_opts)
        return hdfs.create_file(path, f, overwrite=True)


if __name__ == '__main__':
    ho = HdfsOp()
    # res = ho.create_dir('/user/worker/DOTHIS')
    path = '/user/worker/DOTHIS/test.md'
    import codecs

    ho.create_or_overwrite_file(path, None)
