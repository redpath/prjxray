#!/usr/bin/env python3

# https://docs.scipy.org/doc/scipy-0.18.1/reference/generated/scipy.optimize.linprog.html
from scipy.optimize import linprog
from timfuz import Benchmark, Ar_di2np, Ar_ds2t, A_di2ds, A_ds2di, simplify_rows, loadc_Ads_b, index_names, A_ds2np, load_sub, run_sub_json, A_ub_np2d, print_eqns, print_eqns_np
from timfuz_massage import massage_equations
import numpy as np
import glob
import json
import math
from collections import OrderedDict
from fractions import Fraction
import sys
import datetime
import os
import time

def check_feasible(A_ub, b_ub):
    '''
    Put large timing constants into the equations
    See if that would solve it

    Its having trouble giving me solutions as this gets bigger
    Make a terrible baseline guess to confirm we aren't doing something bad
    '''

    sys.stdout.write('Check feasible ')
    sys.stdout.flush()

    rows = len(b_ub)
    cols = len(A_ub[0])

    progress = max(1, rows / 100)

    '''
    Delays should be in order of ns, so a 10 ns delay should be way above what anything should be
    Series can have several hundred delay elements
    Max delay in ballpark
    ''' 
    xs = [1e9 for _i in range(cols)]

    # FIXME: use the correct np function to do this for me
    # Verify bounds
    #b_res = np.matmul(A_ub, xs)
    #print(type(A_ub), type(xs)
    #A_ub = np.array(A_ub)
    #xs = np.array(xs)
    #b_res = np.matmul(A_ub, xs)
    def my_mul(A_ub, xs):
        #print('cols', cols
        #print('rows', rows
        ret = [None] * rows
        for row in range(rows):
            this = 0
            for col in range(cols):
                this += A_ub[row][col] * xs[col]
            ret[row] = this
        return ret
    b_res = my_mul(A_ub, xs)

    # Verify bound was respected
    for rowi, (this_b, this_b_ub) in enumerate(zip(b_res, b_ub)):
        if rowi % progress == 0:
            sys.stdout.write('.')
            sys.stdout.flush()
        if this_b >= this_b_ub or this_b > 0:
            print('% 4d Want res % 10.1f <= % 10.1f <= 0' % (rowi, this_b, this_b_ub))
            raise Exception("Bad ")
    print(' done')

def instances(Ads):
    ret = 0
    for row_ds in Ads:
        ret += sum(row_ds.values())
    return ret

def run(fns_in, corner, run_corner, sub_json=None, dedup=True, massage=False, outfn=None, verbose=False, **kwargs):
    print('Loading data')
    Ads, b = loadc_Ads_b(fns_in, corner, ico=True)

    # Remove duplicate rows
    # is this necessary?
    # maybe better to just add them into the matrix directly
    if dedup:
        oldn = len(Ads)
        iold = instances(Ads)
        Ads, b = simplify_rows(Ads, b)
        print('Simplify %u => %u rows' % (oldn, len(Ads)))
        print('Simplify %u => %u instances' % (iold, instances(Ads)))
        
    if sub_json:
        print('Sub: %u rows' % len(Ads))
        iold = instances(Ads)
        names_old = index_names(Ads)
        run_sub_json(Ads, sub_json, verbose=verbose)
        names = index_names(Ads)
        print("Sub: %u => %u names" % (len(names_old), len(names)))
        print('Sub: %u => %u instances' % (iold, instances(Ads)))
    else:
        names = index_names(Ads)

    if verbose:
        print
        print_eqns(Ads, b, verbose=verbose)

        #print
        #col_dist(A_ubd, 'final', names)

    '''
    Given:
    a >= 10
    a + b >= 100
    A valid solution is:
         a = 100
    However, a better solution is something like
        a = 10
        b = 90
    This creates derived constraints to provide more realistic results 
    '''
    if massage:
        Ads, b = massage_equations(Ads, b)

    print('Converting to numpy...')
    names, Anp = A_ds2np(Ads)
    run_corner(Anp, np.asarray(b), names, outfn=outfn, verbose=verbose, **kwargs)
