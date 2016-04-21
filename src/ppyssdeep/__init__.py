import numpy as np

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

if __name__=='__main__':
    import sys
    content=open(sys.argv[1]).read()
    print ssdeep_hash(content)