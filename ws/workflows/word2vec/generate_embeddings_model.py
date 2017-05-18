from gensim.models.word2vec import *
import codecs, re, json


def train_word2vec(jlines_files, field='title', output_model_file=None, output_jlines_file=None,
                   num_dims=200):
    sentences = list()
    vocab = set()
    for jlines_file in jlines_files:
        print 'starting processing file ', jlines_file
        with codecs.open(jlines_file, 'r', 'utf-8') as f:
            for line in f:
                obj = json.loads(line)
                if field not in obj:
                    continue
                sentence = obj[field]
                # vocab = vocab.union(set(sentence))
                sentences.append(sentence)

    print 'finished reading sentences...'
    model = Word2Vec(sentences=sentences, size=num_dims, window=5, sg=1)
    model.init_sims(replace=True)

    # print model.most_similar(positive=['1', '2', '3'])
    if output_model_file:
        model.save(output_model_file)
    if output_jlines_file:
        out = codecs.open(output_jlines_file, 'w', 'utf-8')
        for item in vocab:
            try:
                answer = dict()
                answer[item] = model[item]
                json.dump(answer, out)
                out.write('\n')
            except:
                print item, ' not in model'
                continue
        out.close()


def serialize_word2vec_model_as_jlines(vocab_file, model_file, jlines_output):
    vocab = list()
    with codecs.open(vocab_file, 'r', 'utf-8') as f:
        for line in f:
            vocab.append(line[0:-1])
    print 'finished reading in vocab: ', str(len(vocab)), ' words'
    model = Word2Vec.load(model_file)
    print 'finished reading in word2vec model'
    out = codecs.open(jlines_output, 'w', 'utf-8')
    not_in = 0
    print model
    for item in vocab:
        try:
            answer = dict()
            answer[item] = model[item].tolist()
            # print model[item].tolist()
            json.dump(answer, out)
            out.write('\n')
        except:
            not_in += 1
            # print item, ' not in model'
            continue
    out.close()
    print 'no. of words not in model...', str(not_in)


def build_vocabulary_from_parts(jlines_files, field='content_strict', output_file=None):
    # sentences = list()
    vocab = set()
    for jlines_file in jlines_files:
        print 'starting processing file ', jlines_file
        with codecs.open(jlines_file, 'r', 'utf-8') as f:
            for line in f:
                obj = json.loads(line)
                if field not in obj:
                    continue
                sentence = obj[field]
                for k in sentence:
                    vocab.add(k)
    out = codecs.open(output_file, 'w', 'utf-8')
    for item in vocab:
        out.write(item)
        out.write('\n')
    out.close()


def word2vec_custom_tester(word2vec_model_file, pos_words):
    """
    Custom file for putting in random stuff.
    :param word2vec_model_file:
    :return:
    """
    model = Word2Vec.load(word2vec_model_file)
    print model.most_similar(positive=pos_words)

    # path = '/Users/mayankkejriwal/Dropbox/dig-memex/memex-hackathon-stuff/memex-may-17/summer_ground_truth_90k_extracted_embeddings/'
    # jlines_files = [path+'part-00000', path+'part-00001', path+'part-00002', path+'part-00003', path+'part-00004',
    #                 path + 'part-00005', path+'part-00006', path+'part-00007', path+'part-00008', path+'part-00009']
    # train_word2vec(jlines_files, output_model_file=path+'all-parts-word2vec-title',
    #                output_jlines_file=None)
    # serialize_word2vec_model_as_jlines(path+'title_vocab.txt', path+'all-parts-word2vec-title',path+'all-parts-word2vec-title.jl')
    # build_vocabulary_from_parts(jlines_files, output_file=path+'cs_vocab.txt')

    # word2vec_custom_tester(path+'all-parts-word2vec-cr', ['charlotte'])
