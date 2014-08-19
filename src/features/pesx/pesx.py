#!/usr/bin/env python

"""
Uses pes[es]262.txt in same directory to identify putative exonic
splice enhancers and supressors (ESEs and ESSs) based upon
octamer subsequences.

Input file should be in the 8+ column format generated by SilVA.

GENE_CACHE is the cache file generated by SilVA that contains 
transcriptome sequences.
"""

# Author: Orion Buske
# Date:   27 December 2011

from __future__ import division, with_statement

import os
import sys
import re

assert os.getenv('SILVA_PATH') is not None, \
       "Error: SILVA_PATH is unset."
sys.path.insert(0, os.path.expandvars("$SILVA_PATH/lib/python"))
from silva import maybe_gzip_open, print_args, get_genes, iter_mutation_seqs

def octamer_subsequences(octs, seq):
    """Return dict: pos -> octamer found in seq"""
    found = dict()
    motif_len = 8  # octamers
    for offset in xrange(0, len(seq) - motif_len + 1):
        target_seq = seq[offset: offset + motif_len]
        if target_seq in octs:
            found[offset] = target_seq

    return found

def score_mutation(octs, old_seq, new_seq):
    """Return differences in oct hits between new and old sequences
    @return: (number of octamers lost, number of octamers gained)
    """
    # octamer_subsequences returns dict of {pos: octamer}
    old = octamer_subsequences(octs, old_seq)
    new = octamer_subsequences(octs, new_seq)
    old_pos = set(old)
    new_pos = set(new)
    return len(old_pos - new_pos), len(new_pos - old_pos)

def read_octamers(filename):
    octs = []
    with open(filename) as ifp:
        for line in ifp:
            line = line.strip()
            if not line or line.startswith('#'): continue
            if len(line) == 8:
                octs.append(line.upper())
            else:
                print >>sys.stderr, "Found invalid octamer: %s" % line
    return set(octs)
                    
def script(gene_cache, filename, pese_filename='pese262.txt',
           pess_filename='pess262.txt', quiet=False, **kwargs):
    pese_set = read_octamers(pese_filename)
    pess_set = read_octamers(pess_filename)
    genes = get_genes(cache_filename=gene_cache)
    fields = ['PESE-', 'PESE+', 'PESS-', 'PESS+']
    if quiet:
        print '#%s' % '\t'.join(fields)
        NULL = '\t'.join(['na'] * len(fields))
    else:
        print '#n_pESE\t+\t-\tn_pESS\t+\t-'
        NULL = '\t'.join(['na'] * 6)
        
    for exon, old, new in iter_mutation_seqs(filename, genes, left=7, right=7):
        n_old_pese = len(octamer_subsequences(pese_set, exon))
        n_old_pess = len(octamer_subsequences(pess_set, exon))
        
        pese_down, pese_up = score_mutation(pese_set, old, new)
        pess_down, pess_up = score_mutation(pess_set, old, new)
        def safe_div(num, denom):
            if num + denom > 0:
                return '%.4f' % (num / (num + denom))
            else:
                return 'na'

        if quiet:
            print '\t'.join([safe_div(pese_down, n_old_pese),
                             safe_div(pese_up, n_old_pese),
                             safe_div(pess_down, n_old_pess),
                             safe_div(pess_up, n_old_pess)])
        else:
            print '\t'.join([str(x) for x in [n_old_pese, pese_down, pese_up,
                                              n_old_pess, pess_down, pess_up]])

def parse_args(args):
    from optparse import OptionParser
    usage = "usage: %prog [options] GENE_CACHE FILT"
    description = __doc__.strip()
    
    parser = OptionParser(usage=usage,
                          description=description)
    parser.add_option("-q", "--quiet", default=False,
                      dest="quiet", action='store_true',
                      help="Quiet output, suitable"
                      " for additional processing")
    options, args = parser.parse_args()

    if len(args) != 2:
        parser.error("Inappropriate number of arguments")

    return options, args


def main(args=sys.argv[1:]):
    options, args = parse_args(args)
    kwargs = dict(options.__dict__)

    if not options.quiet:
        print_args(args, kwargs)
    script(*args, **kwargs)

if __name__ == '__main__':
    sys.exit(main())
