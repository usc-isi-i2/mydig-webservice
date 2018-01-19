import json
import codecs

from optparse import OptionParser

if __name__ == '__main__':
    parser = OptionParser()
    (c_options, args) = parser.parse_args()
    input_path = args[0]
    tld_to_remove = args[1]
    db = json.load(codecs.open(input_path, 'r'))
    dbo = codecs.open('db.json', 'w')

    out = dict()
    for k in db.keys():
        print k, tld_to_remove
        if k != tld_to_remove:
            out[k] = db[k]
    dbo.write(json.dumps(out))