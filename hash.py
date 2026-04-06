#import libraries
import hashlib
import numpy as np
import pandas as pd
import pylab as pl

def hashing(text):
    m = hashlib.sha256()
    m.update(text.encode("utf-8"))
    print(m.hexdigest())