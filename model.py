import tensorflow as tf
import numpy as np
import math

class Word2vec_model():
    def __init__(self, vocab_size=30000, embed_size=300, window_size=5, batch_size=128, 
                       sample_num=100, learning_rate=0.2, learning_decay=0.999):
        self.vocab_size = vocab_size
        self.embed_size = embed_size
        self.window_size = window_size
        self.batch_size = batch_size
        self.sample_num = sample_num
        
        self.learning_rate = tf.Variable(float(learning_rate), trainable=False)
        self.learning_decay = learning_decay
        self.lr_decay_op = self.learning_rate.assign(tf.maximum(0.0001, self.learning_rate*self.learning_decay))

    def create_placeholder(self):
        self.input_word = tf.placeholder(tf.int32, shape=[self.batch_size], name='input')
        self.label_word = tf.placeholder(tf.int32, shape=[self.batch_size, 1], name='label')

        self.test_wordA = tf.placeholder(tf.int32, shape=[5], name='test_A')
        self.test_wordB = tf.placeholder(tf.int32, shape=[5], name='test_B')
        self.test_wordC = tf.placeholder(tf.int32, shape=[5], name='test_C')
        self.test_wordD = tf.placeholder(tf.int32, shape=[5], name='test_D')

    def build_graph(self):
        print('Computing graph is building...', end='')
        
        self.embedding = tf.Variable(tf.random_uniform([self.vocab_size, self.embed_size], -0.5 / self.embed_size, 0.5 / self.embed_size), name='embedding_w')
        input_embed = tf.nn.embedding_lookup(self.embedding, self.input_word)

        nce_w = tf.Variable(tf.truncated_normal([self.vocab_size, self.embed_size], stddev=1.0 / math.sqrt(self.embed_size) ))
        nce_b = tf.Variable(tf.zeros([self.vocab_size]))

        self.loss = tf.reduce_mean(tf.nn.nce_loss(weights=nce_w,
                                             biases=nce_b,
                                             labels=self.label_word,
                                             inputs=input_embed,
                                             num_sampled=self.sample_num,
                                             num_classes=self.vocab_size))
        
        optimizer = tf.train.GradientDescentOptimizer(self.learning_rate)
        self.train_op = optimizer.minimize(self.loss)

        print('[done]')

    def initialize(self):
        print('Initializing model...')
        
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True

        self.sess = tf.Session(config=config)
        self.sess.run(tf.global_variables_initializer())

        self.saver = tf.train.Saver()

        print('[done]')

    def build_test_grap(self):
        embeddedA = tf.nn.embedding_lookup(self.embedding, self.test_wordA)
        embeddedB = tf.nn.embedding_lookup(self.embedding, self.test_wordB)
        embeddedC = tf.nn.embedding_lookup(self.embedding, self.test_wordC)
        embeddedD = tf.nn.embedding_lookup(self.embedding, self.test_wordD) 
        
        inferenceD = embeddedA - embeddedB + embeddedC
        
        norm_D = tf.nn.l2_normalize(embeddedD, dim=1)
        norm_infD = tf.nn.l2_normalize(inferenceD,dim=1)
        
        self.cosine_sim = tf.reduce_sum(norm_D * norm_infD, axis=1)
            
    def train(self, wiki_data, model_type='skipgram', epoch=5, batch_size=128):
        step = 0
        for i in range(epoch):
            batch_gen = wiki_data.batch_generator(batch_size=batch_size, model_type=model_type)

            for input_word, label_word in batch_gen:
                _, loss = self.sess.run([self.train_op, self.loss], feed_dict={self.input_word:input_word, self.label_word:label_word})

                if step != 0 and step % 10000 == 0:
                    lr = self.sess.run(self.lr_decay_op)
                    print('Learning rate: %f'%lr)

                if step != 0 and step % 1000 == 0:
                    print('Epoch %d, Step %d, Loss:%f' % (i, step, loss))
                
                if step % 50000 == 0:
                    self._test(wiki_data, step)

                step += 1

            self.saver.save(self.sess, "model/model_%d" % i)

    def _test(self, wiki_data, step):
        vec_A, vec_B, vec_C, vec_D = wiki_data.get_testdata()
        sim = self.sess.run(self.cosine_sim, feed_dict={self.test_wordA:vec_A,
                                                        self.test_wordB:vec_B,
                                                        self.test_wordC:vec_C,
                                                        self.test_wordD:vec_D})

        print('Testing @ step %d, Similarity:'%step,  sim)

    def get_embedding_layer(self):
        embed_arr = self.sess.run(self.embedding)
        return embed_arr
