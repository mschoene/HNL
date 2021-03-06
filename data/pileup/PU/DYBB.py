import ROOT
import numpy as np
from DataFormats.FWLite import Events, Handle
from CMGTools.RootTools.samples.ComponentCreator import ComponentCreator
from PhysicsTools.Heppy.physicsutils.PileUpSummaryInfo import PileUpSummaryInfo
import os
from multiprocessing import Process
from pdb import set_trace

from CMGTools.HNL.samples.samples_mc_2017_noskim import DYBB

ROOT.gROOT.SetBatch()        # don't pop up canvases

creator = ComponentCreator()


# fill with true interactions

handle  = Handle ('std::vector<PileupSummaryInfo>')
label = ("slimmedAddPileupInfo")

nfiles = len(DYBB.files)
batch = 10
maxend = (nfiles - nfiles%batch) / batch + 1

print('\nnumber of batches: %d' % maxend)

def makehistos(batch, i, maxend):
    totevents = 0
    h_ti = ROOT.TH1F('pileup', 'pileup', 200, 0, 200)
    outfile = ROOT.TFile.Open('pileup_DYBB_batch_%i.root'%i, 'recreate')
    begin  = batch * (i)
    end    = batch * (i+1)

    print 'running of %d-th batch of %d files' %(i+1, batch)

    events = Events(DYBB.files[begin:end])
    for j, event in enumerate(events):
        if j%200000==0:
            print '\t\tprocessing the %d-th event of the %d-th batch' %(j, i+1)
        event.getByLabel(label, handle)
        puinfos = map(PileUpSummaryInfo, handle.product())
        for pu in puinfos:
            if pu.getBunchCrossing()==0:
                try:
                    h_ti.Fill(pu.nTrueInteractions())
                except:
                    print('batch %i failed at event %i'%(i+1,event)); break
                break
    totevents += j
    print '\tprocessed %d events so far' %(events.size())
    proc = os.getpid()
    outfile.cd()
    h_ti.Write()
    outfile.Close()

if __name__ == '__main__':
    procs = []
 
    print('\nenter start batch and end batch\n')
    START = input('start batch: ')
    END = input('end batch: ')

    print('start = %i, end = %i'%(START,END))
    print('press c to continue')
    set_trace()

    for i in range(START,END):
        proc = Process(target=makehistos, args=(batch, i, maxend))
        procs.append(proc)
        proc.start()
 
    for proc in procs:
        proc.join()
