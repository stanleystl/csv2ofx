
import sys, os, time
from traceback import print_exc

from csvutils import *
import ofx, qif, mappings

delimiter = ','

class csv2ofx():    
    def __init__(self):        
        if (len(sys.argv) < 2):
            raise Exception("Csv path must be supplied")

        csv_path = sys.argv[1]
        grid = SimpleCSVGrid(csv_path,delimiter)
        ofx.export(csv_path + ".ofx", mappings.creditcardbradesco['OFX'], grid)

