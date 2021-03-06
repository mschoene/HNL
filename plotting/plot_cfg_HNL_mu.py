import copy
from collections import namedtuple
from operator import itemgetter
from ROOT import gROOT as gr

from shutil import copyfile
from numpy import array

from copy_reg import pickle       # to pickle methods for multiprocessing
from types    import MethodType   # to pickle methods for multiprocessing

from CMGTools.HNL.plotter.PlotConfigs import HistogramCfg, VariableCfg
from CMGTools.HNL.plotter.categories_HNL import cat_Inc
from CMGTools.HNL.plotter.HistCreator import CreateHists, createTrees
from CMGTools.HNL.plotter.HistDrawer import HistDrawer
from CMGTools.HNL.plotter.Variables import hnl_vars, test_vars, getVars, dde_vars
from CMGTools.HNL.samples.samples_mc_2017 import hnl_bkg
from pdb import set_trace
# from CMGTools.HNL.plotter.qcdEstimationMSSMltau import estimateQCDWMSSM, createQCDWHistograms
from CMGTools.HNL.plotter.defaultGroups import createDefaultGroups

from CMGTools.HNL.plotter.Samples import createSampleLists
from CMGTools.HNL.plotter.metrics import ams_hists

######################
# Basic configurations
######################
plotDir = '/eos/user/d/dezhu/HNL/plots/prompt_mu/'
# mode = 'e' 
mode = 'm'

if mode == 'e':
    channel_name = 'e#mu#mu'
if mode == 'm':
    channel_name = '#mu#mu#mu'


def _pickle_method(method): 
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class
    return _unpickle_method, (func_name, obj, cls)

def _unpickle_method(func_name, obj, cls):
    for cls in cls.mro():
        try:
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
    return func.__get__(obj, cls)

pickle(MethodType, _pickle_method, _unpickle_method)

gr.SetBatch(True) # NEEDS TO BE SET FOR MULTIPROCESSING OF plot.Draw()
Cut = namedtuple('Cut', ['name', 'cut'])

int_lumi = 41000.0 # pb #### FIXME 
#int_lumi = 80000.0 # pb #### FIXME 

## RICCARDO
# cuts.append(Cut('ttjetsloose', 'nbj>1'))
# cuts.append(Cut('zmmloose' , 'l1_pt>5  & l2_pt>5  & l1_q!=l2_q & l1_id_t & l2_id_t & l1_reliso05<0.2 & l2_reliso05<0.2 & abs(l1_dz)<0.2 & abs(l2_dz)<0.2 & abs(l1_dxy)<0.045 & abs(l2_dxy)<0.045 & nbj==0 & pass_e_veto & pass_m_veto'))
# cuts.append(Cut('zmmhighpt', 'l1_pt>15  & l2_pt>15  & l1_q!=l2_q & l1_id_t & l2_id_t & l1_reliso05<0.2 & l2_reliso05<0.2 & abs(l1_dz)<0.2 & abs(l2_dz)<0.2 & abs(l1_dxy)<0.045 & abs(l2_dxy)<0.045 & nbj==0 & pass_e_veto & pass_m_veto'))
# cuts.append(Cut('zmm'      , 'l1_pt>10 & l2_pt>10 & l1_q!=l2_q & !l0_eid_mva_iso_loose & l0_reliso05>0.15 & l1_id_t & l2_id_t & l1_reliso05<0.2 & l2_reliso05<0.2 & abs(l1_dz)<0.2 & abs(l2_dz)<0.2 & abs(l1_dxy)<0.045 & abs(l2_dxy)<0.045 & nbj==0 & pass_e_veto & pass_m_veto'))

# cuts.append(Cut('inclusive'    , 'l0_pt>30 & l1_pt>4 & l2_pt>4 & l1_q != l2_q && l0_eid_mva_iso_loose & l0_reliso05<0.15'))
# cuts.append(Cut('inclusive'    , 'l0_pt>30 & l1_pt>4 & l2_pt>4 & l1_q != l2_q && l0_eid_mva_iso_loose & l0_reliso05<0.15 & l1_id_m & l2_id_m & l1_reliso05<0.2 & l2_reliso05<0.2'))
# cuts.append(Cut('inc_nobj'     , 'l0_pt>30 & l1_pt>4 & l2_pt>4 & l1_q != l2_q && l0_eid_mva_iso_loose & l0_reliso05<0.15 & l1_id_m & l2_id_m & l1_reliso05<0.2 & l2_reliso05<0.2 & nbj==0'))
# cuts.append(Cut('inc_nobj_veto', 'l0_pt>30 & l1_pt>4 & l2_pt>4 & l1_q != l2_q && l0_eid_mva_iso_loose & l0_reliso05<0.15 & l1_id_m & l2_id_m & l1_reliso05<0.2 & l2_reliso05<0.2 & nbj==0 & pass_e_veto & pass_m_veto'))
# cuts.append(Cut('stringent'    , 'l0_pt>30 & l1_pt>4 & l2_pt>4 & sv_prob>0.1 & sv_cos>0.9 & hnl_2d_disp_sig>3 & abs(hnl_w_q)==1 & hnl_iso_rel<0.2 & hnl_hn_q==0 & hnl_pt_12>20 & l0_eid_mva_iso_loose & l1_is_oot==0 & l2_is_oot==0 & pass_e_veto & pass_m_veto & l1_id_l & l2_id_l & l0_reliso05<0.2 & nbj==0 & hnl_2d_disp>2'))

### VINZENZ
## CONTROL REGIONS
'''slide 14 - DY:     OSSF pair present; |M_ll - m_Z| < 15 GeV; |M_3l - m_Z| > 15 GeV; 0 b-jets; E_T^miss < 30GeV; M_T < 30GeV
   slide 15 - ttbar:  |M_ll - m_Z| > 15 GeV (if OSSF); |M_3l - m_Z| > 15 GeV (if OSSF); >= 1 b-jets; veto M_ll < 12 GeV (conversion)
   slide 17 - WZ:     OSSF pair present; |M_ll -m_Z|< 15 GeV; |M_3l -m_Z| > 15 GeV; 0 b-jets; E_T^miss > 50 GeV ; p_T > 25, 15, 10 GeV (l0,1,2)
   E_T^Miss == pfmet_pt, M_T == hnl_mt_0 
'''
mz = 91.18; mw = 80.4

ZVeto12    = '  &&  abs(hnl_m_12 - 91.18) > 15'
ZVeto01    = '  &&  abs(hnl_m_01 - 91.18) > 15'
ZVeto02    = '  &&  abs(hnl_m_02 - 91.18) > 15'

CR_DY      = '  &&  abs(hnl_m_12 - 91.18) < 15  &&  abs(hnl_w_vis_m - 91.18) > 15  &&  nbj == 0  &&  pfmet_pt < 30  &&  hnl_mt_0 < 30' 
CR_DY_noMcuts  = '  &&  nbj == 0  &&  pfmet_pt < 30  &&  hnl_mt_0 < 30' 
CR_DYNoM3l = '  &&  abs(hnl_m_12 - 91.18) < 15  &&  nbj == 0  &&  pfmet_pt < 30  &&  hnl_mt_0 < 30' 
CR_DYRic   = 'abs(l0_dz) < 0.2  &&  l1_q != l2_q  &&  l1_pt > 15  &&  l2_pt > 10  &&  abs(hnl_m_12 - 91.18) < 15  &&  nbj == 0' 
CR_DY_3mu_m3muAtZ      = '  && ((abs(hnl_w_vis_m - 91.18) < 15  &&  nbj == 0  &&  pfmet_pt < 50))' 
OSlarge      = '  && ((abs(hnl_w_vis_m - 91.18) < 15  &&  nbj == 0  &&  pfmet_pt < 50) && (hnl_q_01 == 0 && hnl_pt_01 > 5)  && (hnl_q_02 == 0 && hnl_pt_02 > 5)  && (hnl_q_12 == 0 && hnl_pt_12 > 5))' 
CR_DY_3mu_l1l2  = '  &&  ((abs(hnl_m_01 - 91.18) < 10  && hnl_q_01 ==0 && abs(l1_dz) < 0.2 &&  abs(l1_dxy) < 0.045 &&  l1_id_m ) | (abs(hnl_m_02 - 91.18) < 10  && hnl_q_02 ==0 && abs(l2_dz) < 0.2 &&  abs(l2_dxy) < 0.045 &&  l2_id_m ))' 
CR_DY_3mu_l1l2disp  = '  &&  ((abs(hnl_m_01 - 91.18) < 10  && hnl_q_01 ==0) | (abs(hnl_m_02 - 91.18) < 10  && hnl_q_02 ==0))' 
CR_DY_3mu_l1  = '  &&  (abs(hnl_m_01 - 91.18) < 10  && hnl_q_01 ==0 && abs(l1_dz) < 0.2 &&  abs(l1_dxy) < 0.045 &&  l1_id_m )' 

CR_DY_ZZ  = '&&  nbj == 0  &&  pfmet_pt < 50  && ('\
            '(hnl_m_01 > 4 && hnl_m_01 < 75) &&' \
            '(hnl_m_02 > 4 && hnl_m_02 < 75) &&' \
            '(hnl_m_12 > 4 && hnl_m_12 < 75))' \

CR_ttbar   = '  &&  abs(hnl_m_12 - 91.18) > 15  &&  abs(hnl_w_vis_m - 91.18) > 15  &&  nbj >= 1  &&  hnl_m_12 > 12'
CR_ttbarb0 = '  &&  abs(hnl_m_12 - 91.18) > 15  &&  abs(hnl_w_vis_m - 91.18) > 15  &&  nbj == 0  &&  hnl_m_12 > 12'
CR_ttbarb1 = '  &&  abs(hnl_m_12 - 91.18) > 15  &&  abs(hnl_w_vis_m - 91.18) > 15  &&  nbj <= 1  &&  hnl_m_12 > 12'
CR_ttbarb2 = '  &&  abs(hnl_m_12 - 91.18) > 15  &&  abs(hnl_w_vis_m - 91.18) > 15  &&  nbj >= 2  &&  hnl_m_12 > 12'

CR_WZ      = '  &&  abs(hnl_m_12 - 91.18) < 15  &&  abs(hnl_w_vis_m - 91.18) > 15  &&  nbj == 0  &&  pfmet_pt > 50  &&  l0_pt > 25  &&  l1_pt > 15  &&  l2_pt > 10'

CR_WJets       = '  &&  abs(hnl_m_12 - 91.18) > 15  &&  abs(hnl_w_vis_m - 91.18) > 15  &&  nbj == 0  &&  pfmet_pt > 50  &&  hnl_mt_0 > 30  &&  hnl_m_12 > 4'

NaiveSR    = '  &&  hnl_pt_12 > 15  &&  hnl_w_vis_m < 80.4  &&  abs(hnl_m_12 - 91.18) > 10  &&  hnl_iso_rel < 0.2  &&  hnl_2d_disp_sig > 4  &&  l1_id_tnv  &&  l2_id_tnv'
NaiveSRv2  = NaiveSR + '  &&  sv_cos > 0.99  &&  nbj == 0  &&  hnl_w_m > 50  &&  abs(hnl_dphi_hnvis0) > 2  &&  hnl_mt_0 < 60'

prompt_e_loose  = '  &&  l0_eid_mva_noniso_loose'
prompt_e_medium = '  &&  l0_eid_cut_medium'
prompt_e_tight  = '  &&  l0_eid_cut_tight'

prompt_mu_loose  = '  &&  l0_id_l'
prompt_mu_medium = '  &&  l0_id_m'
prompt_mu_tight  = '  &&  l0_id_t'

smalll2eta  = '  && abs(l2_eta)<1.1' 
largel2eta  = '  && abs(l2_eta)>1.1' 
l2_id_m     = '  &&  l1_id_m && l2_id_m ' 
l2_id_l     = '  &&  l1_id_m && l2_id_l ' 

looser  = '  &&  l1_reliso05 < 0.15  &&  l2_reliso05 < 0.15  &&  l1_id_m  &&  l2_id_m'
tighter = '  &&  abs(l1_dz) < 0.2  &&  abs(l2_dz) < 0.2  &&  l1_reliso05 < 0.15  &&  l2_reliso05 < 0.15  &&  l1_id_t  &&  l2_id_t'
veto    = '  &&  pass_e_veto  &&  pass_m_veto'

mvetofail = '  && pass_m_veto == 0' 

imp_par    = '  &&  abs(l1_dz) < 0.2  &&  abs(l2_dz) < 0.2  &&  abs(l1_dxy) < 0.045  &&  abs(l2_dxy) < 0.045' 
IDlNoIso   =  '  &&  l1_id_l  &&  l2_id_l'
IDmNoIso   =  '  &&  l1_id_m  &&  l2_id_m'
IDlIso15   = IDlNoIso   + '  &&  l1_reliso05 < 0.15  &&  l2_reliso05 < 0.15'
IDmIso15   = IDmNoIso   + '  &&  l1_reliso05 < 0.15  &&  l2_reliso05 < 0.15'

d0p5noIDnorIso = '  &&  hnl_2d_disp > 0.5' 
d0p5IDlNoIso   = d0p5noIDnorIso + '  &&  l1_id_l  &&  l2_id_l'                        
d0p5IDmNoIso   = d0p5noIDnorIso + '  &&  l1_id_m  &&  l2_id_m'
d0p5IDlIso15   = d0p5IDlNoIso   + '  &&  l1_reliso05 < 0.15  &&  l2_reliso05 < 0.15'
d0p5IDmIso15   = d0p5IDmNoIso   + '  &&  l1_reliso05 < 0.15  &&  l2_reliso05 < 0.15'

goodVertices                 = '  &&  Flag_goodVertices'    
globalSuperTightHalo2016     = '  &&  Flag_globalSuperTightHalo2016Filter'    
HBHENoise                    = '  &&  Flag_HBHENoiseFilter'                   
HBHENoiseIso                 = '  &&  Flag_HBHENoiseIsoFilter'                
EcalDeadCellTriggerPrimitive = '  &&  Flag_EcalDeadCellTriggerPrimitiveFilter'
BadPFMuon                    = '  &&  Flag_BadPFMuonFilter'                   
BadChargedCandidate          = '  &&  Flag_BadChargedCandidateFilter'         
eeBadSc                      = '  &&  Flag_eeBadScFilter'                     
ecalBadCalib                 = '  &&  Flag_ecalBadCalibFilter'                

met_filtered   = goodVertices + globalSuperTightHalo2016 + HBHENoise + HBHENoiseIso + EcalDeadCellTriggerPrimitive + BadPFMuon + BadChargedCandidate + eeBadSc + ecalBadCalib 

disp1      = '  &&  hnl_2d_disp > 1'
M10 = '  &&  hnl_m_01 > 10  &&  hnl_m_02 > 10  &&  hnl_m_12 > 10'

inc_cut =   'l1_pt > 4  &&  l2_pt > 4  &&  l0_pt > 27' #'.join([cat_Inc])
inc_cut += '  &&  l1_q != l2_q'
inc_cut += '  &&  l0_reliso05 < 0.15'
inc_cut += '  &&  abs(l0_dz) < 0.2'
inc_cut += '  &&  hnl_dr_01 > 0.05  &&  hnl_dr_02 > 0.05' # avoid ele mu mismatching

inc_cut_relxd =   'l1_pt > 4  &&  l2_pt > 4  &&  l0_pt > 35' #'.join([cat_Inc])
inc_cut_relxd += '  &&  abs(l0_dz) < 0.2'
inc_cut_relxd += '  &&  hnl_dr_01 > 0.05  &&  hnl_dr_02 > 0.05' # avoid ele mu mismatching

## equality for all 3 muons
inc_cut_3mu =   'l1_pt > 20  &&  l2_pt > 10  &&  l0_pt > 27'\
                '  &&  abs(l0_dz) < 0.2 &&  abs(l1_dz) < 0.2 &&  abs(l2_dz) < 0.2 '\
                '  &&  abs(l0_dxy) < 0.045 &&  abs(l1_dxy) < 0.045 &&  abs(l2_dxy) < 0.045 '\
                '  && l0_id_m && l1_id_m && l2_id_m '\
                '  && abs(l0_eta) < 2.4 && abs(l1_eta) < 2.4 && abs(l2_eta) < 2.4 '\
                '  && l0_reliso05 < 0.1 && l1_reliso05 < 0.1 && l2_reliso05 < 0.1 '\
                '  && hnl_dr_01 > 0.05 && hnl_dr_02 > 0.05 && hnl_dr_12 > 0.05 '

threeMu_pt_rlxd =   'l1_pt > 20  &&  l2_pt > 4  &&  l0_pt > 4'\
                '  &&  abs(l0_dz) < 0.2 &&  abs(l1_dz) < 0.2 &&  abs(l2_dz) < 0.2 '\
                '  &&  abs(l0_dxy) < 0.045 &&  abs(l1_dxy) < 0.045 &&  abs(l2_dxy) < 0.045 '\
                '  && l0_id_m && l1_id_m && l2_id_m '\
                '  && abs(l0_eta) < 2.4 && abs(l1_eta) < 2.4 && abs(l2_eta) < 2.4 '\
                '  && l0_reliso05 < 0.1 && l1_reliso05 < 0.1 && l2_reliso05 < 0.1 '\
                '  && hnl_dr_01 > 0.05 && hnl_dr_02 > 0.05 && hnl_dr_12 > 0.05 '

iso_cut = 0.15
def LepIDIsoPass(lep, ID, iso_cut):
#    cut_var = ' & l%i_id_%s & l%i_reliso05_03 < %f'%(lep, ID, lep, iso_cut)
    cut_var = ' & l%i_id_%s & l%i_reliso05 < %f'%(lep, ID, lep, iso_cut)
#    cut_var = ' & l%i_id_%s & l%i_reliso_rho_04 < %f'%(lep, ID, lep, iso_cut) ## FROM v2 ON
    return cut_var

def LepIDIsoFail(lep, ID, iso_cut):
#    cut_var = ' & l%i_id_%s & l%i_reliso05_03 > %f'%(lep, ID, lep, iso_cut)
    cut_var = ' & l%i_id_%s & l%i_reliso05 > %f'%(lep, ID, lep, iso_cut)
#    cut_var = ' & l%i_id_%s & l%i_reliso_rho_04 > %f'%(lep, ID, lep, iso_cut) ## FROM v2 ON
    return cut_var

AR_m3lgeq80 = 'abs(l1_jet_pt - l2_jet_pt) < 1 & hnl_w_vis_m > 80 & nbj == 0 & hnl_2d_disp > 0.5 '
AR_m3lgeq80 += LepIDIsoPass(0, 't', iso_cut) + LepIDIsoPass(1, 't', iso_cut) + LepIDIsoPass(2, 't', iso_cut)

TIGHT         = ' & (l1_pt > 3 & l2_pt > 3 & l0_id_t & l0_reliso05 < 0.15 & l1_id_l & l2_id_l & l1_reliso05 < 0.15 & l2_reliso05 < 0.15 )' 
cut_T_APL   = 'abs(l1_jet_pt - l2_jet_pt) < 1 & hnl_dr_12 < 0.8 & hnl_w_vis_m > 80 & nbj == 0 & hnl_2d_disp > 0.5 & abs(l1_dz) < 2 & abs(l2_dz) < 2' + TIGHT

l0_tight = ' & l0_id_t'

def prepareCuts():
    cuts = []
# standard inc_cut from emumu
    inc_cut =   'l1_pt > 4  &&  l2_pt > 4  &&  l0_pt > 27' #'.join([cat_Inc])
    inc_cut += '  &&  l1_q != l2_q'
    inc_cut += '  &&  l0_reliso05 < 0.15'
    inc_cut += '  &&  abs(l0_dz) < 0.2'
    inc_cut += '  &&  hnl_dr_01 > 0.05  &&  hnl_dr_02 > 0.05' # avoid ele mu mismatching

## all 3 muons equal
    inc_cut_3mu =   '  l0_pt > 27 && l1_pt > 20  &&  l2_pt > 10'\
                    '  &&  abs(l0_dz) < 0.2 &&  abs(l1_dz) < 0.2 &&  abs(l2_dz) < 0.2 '\
                    '  &&  abs(l0_dxy) < 0.045 &&  abs(l1_dxy) < 0.045 &&  abs(l2_dxy) < 0.045 '\
                    '  && l0_id_m && l1_id_m && l2_id_m '\
                    '  && abs(l0_eta) < 2.4 && abs(l1_eta) < 2.4 && abs(l2_eta) < 2.4 '\
                    '  && l0_reliso05 < 0.1 && l1_reliso05 < 0.1 && l2_reliso05 < 0.1 '\
                    '  && hnl_dr_01 > 0.05 && hnl_dr_02 > 0.05 && hnl_dr_12 > 0.05 '

    ## RICCARDO
#    cuts.append(Cut('ttjetsloose', 'nbj>1'))
#     cuts.append(Cut('zmmloose' , 'l1_pt>5  & l2_pt>5  & l1_q!=l2_q & l1_id_t & l2_id_t & l1_reliso05<0.2 & l2_reliso05<0.2 & abs(l1_dz)<0.2 & abs(l2_dz)<0.2 & abs(l1_dxy)<0.045 & abs(l2_dxy)<0.045 & nbj==0 & pass_e_veto & pass_m_veto'))
#     cuts.append(Cut('zmmhighpt', 'l1_pt>15  & l2_pt>15  & l1_q!=l2_q & l1_id_t & l2_id_t & l1_reliso05<0.2 & l2_reliso05<0.2 & abs(l1_dz)<0.2 & abs(l2_dz)<0.2 & abs(l1_dxy)<0.045 & abs(l2_dxy)<0.045 & nbj==0 & pass_e_veto & pass_m_veto'))
#     cuts.append(Cut('zmm'      , 'l1_pt>10 & l2_pt>10 & l1_q!=l2_q & !l0_eid_mva_iso_loose & l0_reliso05>0.15 & l1_id_t & l2_id_t & l1_reliso05<0.2 & l2_reliso05<0.2 & abs(l1_dz)<0.2 & abs(l2_dz)<0.2 & abs(l1_dxy)<0.045 & abs(l2_dxy)<0.045 & nbj==0 & pass_e_veto & pass_m_veto'))

#     cuts.append(Cut('inclusive'    , 'l0_pt>30 & l1_pt>4 & l2_pt>4 & l1_q != l2_q && l0_eid_mva_iso_loose & l0_reliso05<0.15'))
#     cuts.append(Cut('inclusive'    , 'l0_pt>30 & l1_pt>4 & l2_pt>4 & l1_q != l2_q && l0_eid_mva_iso_loose & l0_reliso05<0.15 & l1_id_m & l2_id_m & l1_reliso05<0.2 & l2_reliso05<0.2'))
#     cuts.append(Cut('inc_nobj'     , 'l0_pt>30 & l1_pt>4 & l2_pt>4 & l1_q != l2_q && l0_eid_mva_iso_loose & l0_reliso05<0.15 & l1_id_m & l2_id_m & l1_reliso05<0.2 & l2_reliso05<0.2 & nbj==0'))
#     cuts.append(Cut('inc_nobj_veto', 'l0_pt>30 & l1_pt>4 & l2_pt>4 & l1_q != l2_q && l0_eid_mva_iso_loose & l0_reliso05<0.15 & l1_id_m & l2_id_m & l1_reliso05<0.2 & l2_reliso05<0.2 & nbj==0 & pass_e_veto & pass_m_veto'))
#     cuts.append(Cut('stringent'    , 'l0_pt>30 & l1_pt>4 & l2_pt>4 & sv_prob>0.1 & sv_cos>0.9 & hnl_2d_disp_sig>3 & abs(hnl_w_q)==1 & hnl_iso_rel<0.2 & hnl_hn_q==0 & hnl_pt_12>20 & l0_eid_mva_iso_loose & l1_is_oot==0 & l2_is_oot==0 & pass_e_veto & pass_m_veto & l1_id_l & l2_id_l & l0_reliso05<0.2 & nbj==0 & hnl_2d_disp>2'))

    ### VINZENZ
    ## CONTROL REGIONS
    '''slide 14 - DY:     OSSF pair present; |M_ll - m_Z| < 15 GeV; |M_3l - m_Z| > 15 GeV; 0 b-jets; E_T^miss < 30GeV; M_T < 30GeV
       slide 15 - ttbar:  |M_ll - m_Z| > 15 GeV (if OSSF); |M_3l - m_Z| > 15 GeV (if OSSF); >= 1 b-jets; veto M_ll < 12 GeV (conversion)
       slide 17 - WZ:     OSSF pair present; |M_ll -m_Z|< 15 GeV; |M_3l -m_Z| > 15 GeV; 0 b-jets; E_T^miss > 50 GeV ; p_T > 25, 15, 10 GeV (l0,1,2)
       E_T^Miss == pfmet_pt, M_T == hnl_mt_0 
    '''
    mz = 91.18; mw = 80.4

    # CR_DY      = '  &&  abs(hnl_m_12 - 91.18) < 15  &&  abs(hnl_w_vis_m - 91.18) > 15  &&  nbj == 0  &&  pfmet_pt < 30  &&  hnl_mt_0 < 30' 
    # CR_DY_ZZ  = '&&  nbj == 0  &&  pfmet_pt < 50  && ('\
                # '(hnl_q_01 == 0 && hnl_m_01 > 4 && hnl_m_01 < 75) |' \
                # '(hnl_q_02 == 0 && hnl_m_02 > 4 && hnl_m_02 < 75) |' \
                # '(hnl_q_12 == 0 && hnl_m_12 > 4 && hnl_m_12 < 75))' \
    CR_DY_ZZ  = '&&  nbj == 0  &&  pfmet_pt < 50  && ('\
                '(hnl_m_01 > 4 && hnl_m_01 < 75) &&' \
                '(hnl_m_02 > 4 && hnl_m_02 < 75) &&' \
                '(hnl_m_12 > 4 && hnl_m_12 < 75))' \
    # CR_DY_ZZ   = '  &&  nbj == 0  &&  pfmet_pt < 50  &&  hnl_mt_0 < 30 && ((abs(hnl_m_01 - 91.18) < 10  && hnl_q_01 ==0) | (abs(hnl_m_02 - 91.18) < 10  && hnl_q_02 ==0) | (abs(hnl_w_vis_m - 91.18) < 15))' 
    mveto      = '  && pass_m_veto == 0' 
    CR_DYNoM3l = '  &&  abs(hnl_m_12 - 91.18) < 15  &&  nbj == 0  &&  pfmet_pt < 30  &&  hnl_mt_0 < 30' 
    CR_DY_3mu_m3muAtZ      = '  && ((abs(hnl_w_vis_m - 91.18) < 15  &&  nbj == 0  &&  pfmet_pt < 50))' 
    OSlarge      = '  && ((abs(hnl_w_vis_m - 91.18) < 15  &&  nbj == 0  &&  pfmet_pt < 50) && (hnl_q_01 == 0 && hnl_pt_01 > 5)  && (hnl_q_02 == 0 && hnl_pt_02 > 5)  && (hnl_q_12 == 0 && hnl_pt_12 > 5))' 
    CR_DY_3mu_l1l2  = '  &&  ((abs(hnl_m_01 - 91.18) < 10  && hnl_q_01 ==0 && abs(l1_dz) < 0.2 &&  abs(l1_dxy) < 0.045 &&  l1_id_m ) | (abs(hnl_m_02 - 91.18) < 10  && hnl_q_02 ==0 && abs(l2_dz) < 0.2 &&  abs(l2_dxy) < 0.045 &&  l2_id_m ))' 
    CR_DY_3mu_l1l2disp  = '  &&  ((abs(hnl_m_01 - 91.18) < 10  && hnl_q_01 ==0) | (abs(hnl_m_02 - 91.18) < 10  && hnl_q_02 ==0))' 
    CR_DY_3mu_l1  = '  &&  (abs(hnl_m_01 - 91.18) < 10  && hnl_q_01 ==0 && abs(l1_dz) < 0.2 &&  abs(l1_dxy) < 0.045 &&  l1_id_m )' 
    smalll2eta  = '  && abs(l2_eta)<1.1' 
    largel2eta  = '  && abs(l2_eta)>1.1' 
    l2_id_m     = '  &&  l1_id_m && l2_id_m ' 
    l2_id_l     = '  &&  l1_id_m && l2_id_l ' 


    CR_DYRic   = 'abs(l0_dz) < 0.2  &&  l1_q != l2_q  &&  l1_pt > 15  &&  l2_pt > 10  &&  abs(hnl_m_12 - 91.18) < 15  &&  nbj == 0' 
    CR_ttbar   = '  &&  abs(hnl_m_12 - 91.18) > 15  &&  abs(hnl_w_vis_m - 91.18) > 15  &&  nbj >= 1  &&  hnl_m_12 > 12'
    CR_ttbarb0 = '  &&  abs(hnl_m_12 - 91.18) > 15  &&  abs(hnl_w_vis_m - 91.18) > 15  &&  nbj == 0  &&  hnl_m_12 > 12'
    CR_ttbarb1 = '  &&  abs(hnl_m_12 - 91.18) > 15  &&  abs(hnl_w_vis_m - 91.18) > 15  &&  nbj <= 1  &&  hnl_m_12 > 12'
    CR_ttbarb2 = '  &&  abs(hnl_m_12 - 91.18) > 15  &&  abs(hnl_w_vis_m - 91.18) > 15  &&  nbj >= 2  &&  hnl_m_12 > 12'
    CR_WZ      = '  &&  abs(hnl_m_12 - 91.18) < 15  &&  abs(hnl_w_vis_m - 91.18) > 15  &&  nbj == 0  &&  pfmet_pt > 50  &&  l0_pt > 25  &&  l1_pt > 15  &&  l2_pt > 10'
    NaiveSR    = '  &&  hnl_pt_12 > 15  &&  hnl_w_vis_m < 80.4  &&  abs(hnl_m_12 - 91.18) > 10  &&  hnl_iso_rel < 0.2  &&  hnl_2d_disp_sig > 4  &&  l1_id_tnv  &&  l2_id_tnv'
    NaiveSRv2  = NaiveSR + '  &&  sv_cos > 0.99  &&  nbj == 0  &&  hnl_w_m > 50  &&  abs(hnl_dphi_hnvis0) > 2  &&  hnl_mt_0 < 60'

    prompt_e_loose  = '  &&  l0_eid_mva_noniso_loose'
    prompt_e_medium = '  &&  l0_eid_cut_medium'
    prompt_e_tight  = '  &&  l0_eid_cut_tight'
    
    prompt_mu_loose  = '  &&  l0_id_l'
    prompt_mu_medium = '  &&  l0_id_m'
    prompt_mu_tight  = '  &&  l0_id_t'

    looser  = '  &&  l1_reliso05 < 0.15  &&  l2_reliso05 < 0.15  &&  l1_id_m  &&  l2_id_m'
    tighter = '  &&  abs(l1_dz) < 0.2  &&  abs(l2_dz) < 0.2  &&  l1_reliso05 < 0.15  &&  l2_reliso05 < 0.15  &&  l1_id_t  &&  l2_id_t'
    veto    = '  &&  pass_e_veto  &&  pass_m_veto'

    noIDnorIso = '  &&  abs(l1_dz) < 0.2  &&  abs(l2_dz) < 0.2  &&  abs(l1_dxy) < 0.045  &&  abs(l2_dxy) < 0.045' 
    IDlNoIso   = noIDnorIso + '  &&  l1_id_l  &&  l2_id_l'
    IDmNoIso   = noIDnorIso + '  &&  l1_id_m  &&  l2_id_m'
    IDlIso15   = IDlNoIso   + '  &&  l1_reliso05 < 0.15  &&  l2_reliso05 < 0.15'
    IDmIso15   = IDmNoIso   + '  &&  l1_reliso05 < 0.15  &&  l2_reliso05 < 0.15'

    disp1       = '  &&  hnl_2d_disp > 1'
    dispp5      = '  &&  hnl_2d_disp > 0.5'

    if mode == 'e':
        l0_loose  = prompt_e_loose
        l0_medium = prompt_e_medium
        l0_tight  = prompt_e_tight

    if mode == 'm':
        l0_loose  = prompt_mu_loose
        l0_medium = prompt_mu_medium
        l0_tight  = prompt_mu_tight

#### 3.9.
#    cuts.append(Cut('CR_TTbarb0v2', inc_cut + l0_tight + noIDnorIso + CR_ttbarb0))
    # cuts.append(Cut('TTbar_disp1' , inc_cut + l0_tight + CR_ttbar + '  &&  hnl_2d_disp > 1'))

#### 2.9.
#    cuts.append(Cut('CR_TTbarb1_noIDnorIsov2', inc_cut + l0_tight + noIDnorIso + CR_ttbarb1))
#    cuts.append(Cut('CR_TTbarb1_IDlNoIsov2'  , inc_cut + l0_tight + IDlNoIso   + CR_ttbarb1))
#    cuts.append(Cut('CR_TTbarb1_IDlIso15v2'  , inc_cut + l0_tight + IDlIso15   + CR_ttbarb1))
#    cuts.append(Cut('CR_TTbarb2_noIDnorIsov2', inc_cut + l0_tight + noIDnorIso + CR_ttbarb2))
#    cuts.append(Cut('CR_TTbarb2_IDlNoIsov2'  , inc_cut + l0_tight + IDlNoIso   + CR_ttbarb2))
#    cuts.append(Cut('CR_TTbarb2_IDlIso15v2'  , inc_cut + l0_tight + IDlIso15   + CR_ttbarb2))
# 
#    cuts.append(Cut('CR_WZ_noIDnorIsov2'   , inc_cut + l0_tight + noIDnorIso + CR_WZ))
#    cuts.append(Cut('CR_WZ_IDmNoIsov2'   , inc_cut + l0_tight + IDmNoIso + CR_WZ))
#    cuts.append(Cut('CR_WZ_IDmIso15v2'   , inc_cut + l0_tight + IDmIso15 + CR_WZ))
#    cuts.append(Cut('CR_WZ_IDlNoIsov2'   , inc_cut + l0_tight + IDlNoIso + CR_WZ))
#    cuts.append(Cut('CR_WZ_IDlIso15v2'   , inc_cut + l0_tight + IDlIso15 + CR_WZ))

#### 1.9.
### testing multiprocessing
#    cuts.append(Cut('test_multi_ttbar', inc_cut + l0_tight + noIDnorIso + CR_ttbarb0))
#    cuts.append(Cut('test_multi', inc_cut + l0_tight + tighter))
### doing things again with new hnl_dr_01>0.05 and hnl_dr_02>0.05 and updated binning for reliso (up to 0.5) 
#    cuts.append(Cut('NaiveSRv3'          , inc_cut + l0_tight + NaiveSRv2))
#    cuts.append(Cut('CR_DY_noIDnorIsov2'   , inc_cut + l0_tight + noIDnorIso + CR_DY + veto))
#    cuts.append(Cut('CR_DY_IDmNoIsov2'   , inc_cut + l0_tight + IDmNoIso + CR_DY + veto))
#    cuts.append(Cut('CR_DY_IDmIso15v2'   , inc_cut + l0_tight + IDmIso15 + CR_DY + veto))
#    cuts.append(Cut('CR_DYNoM3l_IDlNoIsov2'  , inc_cut + l0_tight + CR_DYNoM3l + veto + IDlNoIso))
#    cuts.append(Cut('CR_DYNoM3l_IDlIso15v2'  , inc_cut + l0_tight + CR_DYNoM3l + veto + IDlIso15))

#    cuts.append(Cut('CR_TTbar_noIDnorIsov2', inc_cut + l0_tight + noIDnorIso + CR_ttbar))
#    cuts.append(Cut('CR_TTbar_IDmNoIsov2', inc_cut + l0_tight + IDmNoIso + CR_ttbar))
#    cuts.append(Cut('CR_TTbar_IDmIso15v2', inc_cut + l0_tight + IDmIso15 + CR_ttbar))

#### 31.8.
#    cuts.append(Cut('CR_TTbarb0_noIDnorIso', inc_cut + l0_tight + noIDnorIso + CR_ttbarb0))

#### 30.8.
###  morning
#    cuts.append(Cut('tight_noIDnorIso'     , inc_cut + l0_tight + noIDnorIso))
#    cuts.append(Cut('CR_DYRic'             , CR_DYRic + looser))
#    cuts.append(Cut('CR_DYNoM3l_noIDnorIso', inc_cut + l0_tight + CR_DYNoM3l + veto + noIDnorIso))
#    cuts.append(Cut('CR_DYNoM3l_IDmNoIso'  , inc_cut + l0_tight + CR_DYNoM3l + veto + IDmNoIso))
#    cuts.append(Cut('CR_DYNoM3l_IDmIso15'  , inc_cut + l0_tight + CR_DYNoM3l + veto + IDmIso15))
#    cuts.append(Cut('NaiveSR'              , inc_cut + l0_tight + NaiveSR))
###  afternoon
#    cuts.append(Cut('CR_DYNoM3l_IDlNoIso'  , inc_cut + l0_tight + CR_DYNoM3l + veto + IDlNoIso))
#    cuts.append(Cut('CR_DYNoM3l_IDlIso15'  , inc_cut + l0_tight + CR_DYNoM3l + veto + IDlIso15))
#    cuts.append(Cut('CR_TTbarb2_noIDnorIso', inc_cut + l0_tight + noIDnorIso + CR_ttbarb2))
#    cuts.append(Cut('CR_TTbarb2_IDlNoIso'  , inc_cut + l0_tight + IDlNoIso   + CR_ttbarb2))
#    cuts.append(Cut('CR_TTbarb2_IDlIso15'  , inc_cut + l0_tight + IDlIso15   + CR_ttbarb2))
#    cuts.append(Cut('NaiveSRv2'            , inc_cut + l0_tight + NaiveSRv2))
#    cuts.append(Cut('CR_WZ_IDlNoIso'   , inc_cut + l0_tight + IDlNoIso + CR_WZ))
#    cuts.append(Cut('CR_WZ_IDlIso15'   , inc_cut + l0_tight + IDlIso15 + CR_WZ))
###  night
#    cuts.append(Cut('CR_TTbarb1_noIDnorIso', inc_cut + l0_tight + noIDnorIso + CR_ttbarb1))
#    cuts.append(Cut('CR_TTbarb1_IDlNoIso'  , inc_cut + l0_tight + IDlNoIso   + CR_ttbarb1))
#    cuts.append(Cut('CR_TTbarb1_IDlIso15'  , inc_cut + l0_tight + IDlIso15   + CR_ttbarb1))

####  29.8.
#    cuts.append(Cut('CR_DY_noIDnorIso'   , inc_cut + l0_tight + noIDnorIso + CR_DY + veto))
#    cuts.append(Cut('CR_TTbar_noIDnorIso', inc_cut + l0_tight + noIDnorIso + CR_ttbar))
#    cuts.append(Cut('CR_WZ_noIDnorIso'   , inc_cut + l0_tight + noIDnorIso + CR_WZ))

#    cuts.append(Cut('CR_DY_IDmNoIso'   , inc_cut + l0_tight + IDmNoIso + CR_DY + veto))
#    cuts.append(Cut('CR_TTbar_IDmNoIso', inc_cut + l0_tight + IDmNoIso + CR_ttbar))
#    cuts.append(Cut('CR_WZ_IDmNoIso'   , inc_cut + l0_tight + IDmNoIso + CR_WZ))

#    cuts.append(Cut('CR_DY_IDmIso15'   , inc_cut + l0_tight + IDmIso15 + CR_DY + veto))
#    cuts.append(Cut('CR_TTbar_IDmIso15', inc_cut + l0_tight + IDmIso15 + CR_ttbar))
#    cuts.append(Cut('CR_WZ_IDmIso15'   , inc_cut + l0_tight + IDmIso15 + CR_WZ))

#    cuts.append(Cut('CR_DY', inc_cut + l0_loose + looser + CR_DY))
#    cuts.append(Cut('CR_TTbar', inc_cut + l0_loose + looser + CR_ttbar))
#    cuts.append(Cut('CR_WZ', inc_cut + l0_loose + looser + CR_WZ))
 
#### 24.8.
#    cuts.append(Cut('looser', inc_cut + l0_loose + '  &&  l1_id_m & l2_id_m'))
#    cuts.append(Cut('tighter_e_loose', inc_cut + l0_loose + tighter))
#    cuts.append(Cut('tighter_e_medium', inc_cut + l0_medium' + tighter))
#    cuts.append(Cut('tighter_e_tight', inc_cut + l0_tight + tighter))

    l0_loose  = prompt_mu_loose
    l0_medium = prompt_mu_medium
    l0_tight  = prompt_mu_tight

#### 10.10.
#    cuts.append( Cut('AR_m3lgeq80_v2',  cut_T_APL) )         
#    cuts.append( Cut('AR_m3lgeq80_v3',  cut_T_APL + ' & hnl_hn_vis_pt > 35') )         
#    cuts.append(Cut('CR_TTbar_imp_par' , inc_cut + l0_tight + imp_par  + CR_ttbar))
#    cuts.append(Cut('CR_TTbar_IDmNoIso', inc_cut + l0_tight + IDmNoIso + CR_ttbar))
    cuts.append(Cut('CR_TTbar_IDmIso15', inc_cut + l0_tight + IDmIso15 + CR_ttbar))
#    cuts.append(Cut('CR_TTbar_imp_par_disp' , inc_cut + l0_tight + imp_par  + CR_ttbar + ' & hnl_2d_disp > 0.5'))
#    cuts.append(Cut('CR_TTbar_IDmNoIso_disp', inc_cut + l0_tight + IDmNoIso + CR_ttbar + ' & hnl_2d_disp > 0.5'))
#    cuts.append(Cut('CR_TTbar_IDmIso15_disp', inc_cut + l0_tight + IDmIso15 + CR_ttbar + ' & hnl_2d_disp > 0.5'))

#### 10.10.
#    cuts.append( Cut('AR_m3lgeq80',  AR_m3lgeq80) )         

#### 19.9.
#    cuts.append(Cut('CR_DY_ZZ_3mu_pt_rlxd',         threeMu_pt_rlxd + CR_DY_ZZ + M10))
#    cuts.append(Cut('CR_DY_m3muAtZ_3mu_pt_rlxd',    threeMu_pt_rlxd  + CR_DY_3mu_m3muAtZ + M10))
#    cuts.append(Cut('no_sel', '1'))

#### 18.9.
#    cuts.append(Cut('CR_WJets_IDlNoIso'         , inc_cut_relxd + l0_tight + IDlNoIso + CR_WJets + '  &&  hnl_dr_12 < 0.4  &&  hnl_dr_hnvis0 > 1' + ZVeto01 + ZVeto02)) # NO IMP PAR! !!CHANGED!!
#    cuts.append(Cut('CR_DY_IDlNoIso'            , inc_cut_relxd + l0_tight + IDlNoIso + CR_DY)) # NO IMP PAR! !!CHANGED!!
#    cuts.append(Cut('CR_DY_noMcuts'            , inc_cut + imp_par + l0_tight + CR_DY_noMcuts + veto))
#    cuts.append(Cut('CR_DY_3muequal_m3muAtZ',    inc_cut_3mu + CR_DY_3mu_m3muAtZ))
#    cuts.append(Cut('CR_DY_small2eta_mveto',    inc_cut_3mu + CR_DY_ZZ + smalll2eta + mvetofail))
#    cuts.append(Cut('CR_DY_ZZ',    inc_cut_3mu + CR_DY_ZZ))
#    cuts.append(Cut('no_sel', '1'))
#    cuts.append(Cut('CR_DY_ZZ_3mu_rlxd',    threeMu_pt_rlxd + CR_DY_ZZ))

#### 13.9.
#    cuts.append(Cut('CR_WJets_IDlNoIso'         , inc_cut_relxd + l0_tight + IDlNoIso + CR_WJets + '  &&  hnl_dr_12 < 0.4  &&  hnl_dr_hnvis0 > 1' + ZVeto01 + ZVeto02)) # NO IMP PAR! !!CHANGED!!

#### 10.9.
#    cuts.append(Cut('CR_DY_3muequal_m3muAtZ',    inc_cut_3mu + CR_DY_3mu_m3muAtZ))
#    cuts.append(Cut('CR_DY_small2eta_mveto',    inc_cut_3mu + CR_DY_ZZ + smalll2eta + mveto))
#    cuts.append(Cut('CR_DY_ZZ',    inc_cut_3mu + CR_DY_ZZ))
#    cuts.append(Cut('CR_WJets_noIDnorIso'       , inc_cut_relxd + l0_tight + imp_par     + CR_WJets + '  &&  hnl_dr_12 < 0.4  &&  hnl_dr_hnvis0 > 1' + ZVeto01 + ZVeto02))
#    cuts.append(Cut('CR_WJets_IDlNoIso'         , inc_cut_relxd + l0_tight + IDlNoIso    + CR_WJets + '  &&  hnl_dr_12 < 0.4  &&  hnl_dr_hnvis0 > 1' + ZVeto01 + ZVeto02))
#    cuts.append(Cut('CR_WJets_IDlIso15'         , inc_cut_relxd + l0_tight + IDlIso15    + CR_WJets + '  &&  hnl_dr_12 < 0.4  &&  hnl_dr_hnvis0 > 1' + ZVeto01 + ZVeto02))

#### 06.9.
    # cuts.append(Cut('CR_DY_l0tight_3mu_l1',            inc_cut + l0_tight + CR_DY_3mu_l1))
    # cuts.append(Cut('CR_DY_l0tight_3mu_l1l2',    inc_cut + l0_tight + CR_DY_3mu_l1l2))
    # cuts.append(Cut('CR_DY_l0tight_3mu_l1l2_dispp5',    inc_cut + l0_tight + CR_DY_3mu_l1l2 + dispp5))
    # cuts.append(Cut('CR_DY_l0tight_3mu_l1l2_small2eta',    inc_cut + l0_tight + CR_DY_3mu_l1l2 + smalll2eta))
    # cuts.append(Cut('CR_DY_l0tight_3mu_l1l2_dispp5',    inc_cut + l0_tight + CR_DY_3mu_l1l2 + dispp5))
    # cuts.append(Cut('CR_DY_l0tight_3mu_l1l2disp_largel2eta_dispp5',    inc_cut + l0_tight + CR_DY_3mu_l1l2disp + largel2eta + dispp5))
    # cuts.append(Cut('CR_DY_l0tight_3mu_l1l2disp_dispp5',    inc_cut + l0_tight + CR_DY_3mu_l1l2disp + largel2eta + dispp5))
    # cuts.append(Cut('CR_DY_l0tight_3mu_l1l2_l2_id_m',    inc_cut + l0_tight + CR_DY_3mu_l1l2 + l2_id_m))
    # cuts.append(Cut('CR_DY_l0tight_3mu_l1l2_l2_id_l',    inc_cut + l0_tight + CR_DY_3mu_l1l2 + l2_id_l))
    # cuts.append(Cut('CR_DY_l0tight_3mu_l2_id_l',    inc_cut + l0_tight + CR_DY_3mu_l1 + l2_id_l))
    # cuts.append(Cut('CR_DY_l0tight_3mu_m3muAtZ',    inc_cut + l0_tight + CR_DY_3mu_m3muAtZ + smalll2eta))
    # cuts.append(Cut('CR_DY_l0tight_3muequal_m3muAtZ_v2',    inc_cut_3mu + l0_tight + CR_DY_3mu_m3muAtZ + smalll2eta))
    # cuts.append(Cut('CR_DY_l0tight_3muequal_l1l2_small2eta',    inc_cut_3mu + l0_tight + CR_DY_3mu_l1l2 + smalll2eta))

#### 20180910
    # cuts.append(Cut('CR_DY_3muequal_m3muAtZ',    inc_cut_3mu + CR_DY_3mu_m3muAtZ))
    # cuts.append(Cut('CR_DY_small2eta_mveto',    inc_cut_3mu + CR_DY_ZZ + smalll2eta + mveto))
    cuts.append(Cut('CR_DY_ZZ_v2',    inc_cut_3mu + CR_DY_ZZ))



    return cuts

def createSamples(analysis_dir, total_weight, qcd_from_same_sign, w_qcd_mssm_method, r_qcd_os_ss, add_data_cut=None, mode='m'):
    hist_dict = {}
    sample_dict = {}
#    set_trace()
    samples_mc, samples_data, samples, all_samples, sampleDict = createSampleLists(analysis_dir=analysis_dir, add_data_cut=add_data_cut, channel=mode)
    
    sample_dict['all_samples'] = all_samples
#    sample_dict['samples_essential'] = samples_essential

    return sample_dict, hist_dict

def createVariables(rebin=None):
    DoNotRebin = ['_norm_', 'n_vtx', 'nj', 'nbj', 'hnl_m_12_wide'] 
    variables = hnl_vars
#    variables = dde_vars
    if rebin>0:
        for ivar in hnl_vars:
            if ivar.name in DoNotRebin: continue
            ivar.binning['nbinsx'] = int(ivar.binning['nbinsx']/rebin)

    return variables

def makePlots(variables, cuts, total_weight, sample_dict, hist_dict, qcd_from_same_sign, w_qcd_mssm_method, mt_cut, friend_func, dc_postfix, make_plots=True, create_trees=False):
    ams_dict = {}
    sample_names = set()
    for cut in cuts:
        cfg_main = HistogramCfg(name=cut.name, var=None, cfgs=sample_dict['all_samples'], cut=cut.cut, lumi=int_lumi, weight=total_weight)
        # cfg_main = HistogramCfg(name=cut.name, var=None, cfgs=sample_dict['samples_essential'], cut=cut.cut, lumi=int_lumi, weight=total_weight)
    
        cfg_main.vars = variables
        HISTS = CreateHists(cfg_main)

        plots = HISTS.createHistograms(cfg_main, verbose=False, friend_func=friend_func)
        #plots.legendPos = 'right'
        for variable in variables:
        # for plot in plots.itervalues():
            plot = plots[variable.name]
            plot.Group('data_obs', ['data_2017B', 'data_2017C', 'data_2017D', 'data_2017E', 'data_2017F'])
            plot.Group('single t', ['ST_tW_at_5f_incD', 'ST_tW_t_5f_incD'])
#            plot.Group('Diboson', ['WZTo3LNu', 'ZZTo4L', 'WWTo2L2Nu'])
            plot.Group('Diboson', ['WZTo3LNu', 'WWTo2L2Nu'])
            plot.Group('Triboson', ['ZZZ', 'WWW', 'WGGJets,WWZ,WZZ'])
            plot.Group('ttV', ['TTZToLLNuNu', 'TTWJetsToLNu'])
            plot.Group('QCD',['QCD_pt_15to20_mu', 'QCD_pt_20to30_mu', 'QCD_pt_30to50_mu', 'QCD_pt_50to80_mu', 'QCD_pt_80to120_mu'])
            plot.Group('WJets', ['W1JetsToLNu', 'W2JetsToLNu', 'W3JetsToLNu', 'W4JetsToLNu'])
#            plot.Group('DY', ['DYJetsToLL_M10to50', 'DYJets_ext'])
            plot.Group('DYJetsToLL_M10to50', ['DYJetsToLL_M10to50', 'DYJetsToLL_M10to50_ext'])
            createDefaultGroups(plot)
            if make_plots:
                HistDrawer.draw(plot,channel = channel_name, plot_dir = plotDir+cut.name)#plot_dir='plots/'+cut.name)

    print '\nOptimisation results:'
    all_vals = ams_dict.items()
    for sample_name in sample_names:
        vals = [v for v in all_vals if sample_name + '_' in v[0]]
        vals.sort(key=itemgetter(1))
        for key, item in vals:
            print item, key

        print '\nBy variable'
        for variable in variables:
            name = variable.name
            print '\nResults for variable', name
            for key, item in vals:
                if key.startswith(name + '__'):
                    print item, key

if __name__ == '__main__':
        
    friend_func = None
    
    qcd_from_same_sign = True
    w_qcd_mssm_method = True
    r_qcd_os_ss = 1.17

    run_central = True
    add_ttbar_sys = False
    add_tes_sys = False

    analysis_dir = '/eos/user/v/vstampf/ntuples/'

    total_weight = 'weight * lhe_weight'

    print total_weight

    cuts = prepareCuts(mode)

    variables = createVariables()#2)

    sample_dict, hist_dict = createSamples(analysis_dir, total_weight, qcd_from_same_sign=False, w_qcd_mssm_method=False, r_qcd_os_ss=None)
    makePlots(
        variables, 
        cuts, 
        total_weight, 
        sample_dict, 
        hist_dict={}, 
        qcd_from_same_sign=False, 
        w_qcd_mssm_method=False, 
        mt_cut='', 
        friend_func=lambda f: f.replace('TESUp', 'TESUpMultiMVA'), 
        dc_postfix='_CMS_scale_t_mt_13TeVUp', 
        make_plots=True
    )

    for i in cuts:
        copyfile('plot_cfg_HNL_mu.py', plotDir+i.name+'/plot_cfg.py')
