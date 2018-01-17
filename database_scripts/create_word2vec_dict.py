# coding: utf-8
from __future__ import division

import struct
import sys

FILE_NAME = "assets/GoogleNews-vectors-negative300.bin"
FLOAT_SIZE = 4 # 32bit float

from collections import defaultdict
get_word = defaultdict(bool)

min_word_length=4
with open('words.txt', 'r') as f:
    words = []
    for line in f:
        line = line.strip().lower()
        if(len(line) >= min_word_length):
            words.append(line)
            get_word[line] = True

vectors = dict()

with open(FILE_NAME, 'rb') as f:
    
    c = None
    
    # read the header
    header = ""
    while c != "\n":
        c = f.read(1)
        header += c

    total_num_vectors, vector_len = (int(x) for x in header.split())
    num_vectors = total_num_vectors
    
    print "Number of vectors: %d/%d" % (num_vectors, total_num_vectors)
    print "Vector size: %d" % vector_len

    for i in xrange(num_vectors):

        word = ""        
        while True:
            c = f.read(1)
            if c == " ":
                break
            word += c

        boolean_val = get_word[word]
        binary_vector = f.read(FLOAT_SIZE * vector_len)

        if(boolean_val):
            vectors[word] = [ struct.unpack_from('f', binary_vector, i)[0] 
                              for i in xrange(0, len(binary_vector), FLOAT_SIZE) ]
        
        sys.stdout.write("%d%%\r" % (len(vectors) / len(words) * 100))
        sys.stdout.flush()

import cPickle

print "\nSaving..."
with open(FILE_NAME[:-3] + "pcl", 'wb') as f:
    cPickle.dump(vectors, f, cPickle.HIGHEST_PROTOCOL)