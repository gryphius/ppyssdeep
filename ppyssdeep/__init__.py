import numpy as np
from ppyssdeep.wagnerfischerpp import WagnerFischer

FNV_PRIME = 0x01000193
FNV_INIT  = 0x28021967
MAX_LENGTH = 64
B64="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

class Last7chars(object):
    def __init__(self):
        self._reset_rollhash()

    def _reset_rollhash(self):
        self.roll_h1 =0
        self.roll_h2 = 0
        self.roll_h3 = 0
        self.ringbuffer = [0]*7
        self.writeindex=0

    def _roll_hash(self,char):
        char7bf=self.readwrite(char)
        self.roll_h2 += 7 * char - self.roll_h1
        self.roll_h1 += char - char7bf
        self.roll_h3 <<= 5
        self.roll_h3 &= 0xffffffff
        self.roll_h3 ^= char
        return self.roll_h1 + self.roll_h2 + self.roll_h3

    def readwrite(self,num):
        retval=self.ringbuffer[self.writeindex]
        self.ringbuffer[self.writeindex]=num
        self.writeindex=(self.writeindex+1)%7
        return retval

    def __repr__(self):
        arr=self.ringbuffer[self.writeindex:]+self.ringbuffer[:self.writeindex]
        return " ".join(map(str,arr))

def _update_fnv(fnvhasharray,newchar):
    fnvhasharray *= FNV_PRIME
    fnvhasharray &= 0xffffffff
    fnvhasharray ^= newchar
    return fnvhasharray

def _calc_initbs(length):
    bs = 3
    while bs * MAX_LENGTH < length:
        bs *=2

    if bs > 3: #proably checking for integer overflow here?
        return bs
    return 3

def ssdeep_hash(content):
    bs = _calc_initbs(len(content))
    hash1 = ''
    hash2 = ''

    last7chars = Last7chars()

    while True:
        last7chars._reset_rollhash()
        fnv1 = FNV_INIT
        fnv2 = FNV_INIT
        hash1 = ''
        hash2 = ''
        fnvarray=np.array([fnv1,fnv2])

        for i in range(len(content)):
            c = ord(content[i])
            h = last7chars._roll_hash(c)
            fnvarray=_update_fnv(fnvarray,c)

            if h%bs == (bs-1) and len(hash1)<(MAX_LENGTH-1):
                b64char = B64[fnvarray[0] & 63]
                hash1 += b64char
                fnvarray[0] = FNV_INIT

            if h % ( 2 * bs ) == ( 2 * bs - 1 ) and len(hash2) < (MAX_LENGTH / 2 - 1):
                b64char = B64[fnvarray[1] & 63]
                hash2 += b64char
                fnvarray[1] = FNV_INIT

        hash1 += B64[fnvarray[0] & 63]
        hash2 += B64[fnvarray[1] & 63]

        if bs <=3 or len(hash1)> (MAX_LENGTH/2):
            break
        bs = int ( bs/2)
        if bs <3:
            bs=3

    return ':'.join([str(bs),hash1,hash2])

#from https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Longest_common_substring#Python_2
def longest_common_substring(s1, s2):
    m = [[0] * (1 + len(s2)) for i in xrange(1 + len(s1))]
    longest, x_longest = 0, 0
    for x in xrange(1, 1 + len(s1)):
        for y in xrange(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
                if m[x][y] > longest:
                    longest = m[x][y]
                    x_longest = x
            else:
                m[x][y] = 0
    return s1[x_longest - longest: x_longest]

def _likeliness(min_lcs, a, b):

    if longest_common_substring(a,b)<min_lcs:
        return 0

    dist = WagnerFischer(a,b).cost
    dist = int(dist * MAX_LENGTH / (len(a) + len(b)))
    dist = int(100* dist/64)
    if dist > 100:
        dist = 100
    return 100 - dist

def ssdeep_compare(hashA, hashB, min_lcs = 7):
    bsA,hs1A,hs2A = hashA.split(':') #blocksize, hash1, hash2
    bsB,hs1B,hs2B = hashB.split(':')
    
    bsA = int(bsA)
    bsB = int(bsB)
    
    like = 0

    #block size comparison
    if bsA == bsB:
        #compare both hashes
        like1 = _likeliness(min_lcs,hs1A, hs1B)
        like2 = _likeliness(min_lcs, hs2A, hs2B)
        like = max(like1,like2)
    elif bsA == 2*bsB:
        # Compare hash_bsA with hash_2*bsB
        like = _likeliness( min_lcs, hs1A, hs2B );
    elif 2*bsA == bsB:
        # Compare hash_2*bsA with hash_bsB
        like = _likeliness( min_lcs, hs2A, hs1B );
    else : #nothing suitable to compare
        like = 0
    return like


if __name__=='__main__':
    import sys
    content1=open('/tmp/file1.txt').read()
    content2=open('/tmp/file2.txt').read()
    hash1=ssdeep_hash(content1)
    print hash1
    hash2=ssdeep_hash(content2)
    print hash2
    similarity = ssdeep_compare(hash1,hash2)
    print similarity
