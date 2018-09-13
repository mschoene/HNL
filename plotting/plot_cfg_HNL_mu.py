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
from CMGTools.HNL.plotter.Variables import hnl_vars, getVars
from CMGTools.HNL.samples.samples_mc_2017 import hnl_bkg
from pdb import set_trace
# from CMGTools.HNL.plotter.qcdEstimationMSSMltau import estimateQCDWMSSM, createQCDWHistograms
from CMGTools.HNL.plotter.defaultGroups import createDefaultGroups

from CMGTools.HNL.plotter.Samples import createSampleLists
from CMGTools.HNL.plotter.metrics import ams_hists

######################
# Basic configurations
######################
plotDir = '/eos/user/v/vstampf/ntuples/plots/prompt_mu/'
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

def prepareCuts(mode):
    cuts = []
    inc_cut =   'l1_pt > 4  &&  l2_pt > 4  &&  l0_pt > 35' #'.join([cat_Inc])
    inc_cut += '  &&  l1_q != l2_q'
    inc_cut += '  &&  l0_reliso05 < 0.15'
    inc_cut += '  &&  abs(l0_dz) < 0.2'
    inc_cut += '  &&  hnl_dr_01 > 0.05  &&  hnl_dr_02 > 0.05' # avoid ele mu mismatching

    inc_cut_relxd =   'l1_pt > 4  &&  l2_pt > 4  &&  l0_pt > 35' #'.join([cat_Inc])
    inc_cut_relxd += '  &&  abs(l0_dz) < 0.2'
    inc_cut_relxd += '  &&  hnl_dr_01 > 0.05  &&  hnl_dr_02 > 0.05' # avoid ele mu mismatching

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

    ZVeto12    = '  &&  abs(hnl_m_12 - 91.18) > 15'
    ZVeto01    = '  &&  abs(hnl_m_01 - 91.18) > 15'
    ZVeto02    = '  &&  abs(hnl_m_02 - 91.18) > 15'

    CR_DY      = '  &&  abs(hnl_m_12 - 91.18) < 15  &&  abs(hnl_w_vis_m - 91.18) > 15  &&  nbj == 0  &&  pfmet_pt < 30  &&  hnl_mt_0 < 30' 
    CR_DYNoM3l = '  &&  abs(hnl_m_12 - 91.18) < 15  &&  nbj == 0  &&  pfmet_pt < 30  &&  hnl_mt_0 < 30' 
    CR_DYRic   = 'abs(l0_dz) < 0.2  &&  l1_q != l2_q  &&  l1_pt > 15  &&  l2_pt > 10  &&  abs(hnl_m_12 - 91.18) < 15  &&  nbj == 0' 
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

    looser  = '  &&  l1_reliso05 < 0.15  &&  l2_reliso05 < 0.15  &&  l1_id_m  &&  l2_id_m'
    tighter = '  &&  abs(l1_dz) < 0.2  &&  abs(l2_dz) < 0.2  &&  l1_reliso05 < 0.15  &&  l2_reliso05 < 0.15  &&  l1_id_t  &&  l2_id_t'
    veto    = '  &&  pass_e_veto  &&  pass_m_veto'

    noIDnorIso = '  &&  abs(l1_dz) < 0.2  &&  abs(l2_dz) < 0.2  &&  abs(l1_dxy) < 0.045  &&  abs(l2_dxy) < 0.045' 
    IDlNoIso   = noIDnorIso + '  &&  l1_id_l  &&  l2_id_l'
    IDmNoIso   = noIDnorIso + '  &&  l1_id_m  &&  l2_id_m'
    IDlIso15   = IDlNoIso   + '  &&  l1_reliso05 < 0.15  &&  l2_reliso05 < 0.15'
    IDmIso15   = IDmNoIso   + '  &&  l1_reliso05 < 0.15  &&  l2_reliso05 < 0.15'

    disp1      = '  &&  hnl_2d_disp > 1'

    if mode == 'e':
        l0_loose  = prompt_e_loose
        l0_medium = prompt_e_medium
        l0_tight  = prompt_e_tight

    if mode == 'm':
        l0_loose  = prompt_mu_loose
        l0_medium = prompt_mu_medium
        l0_tight  = prompt_mu_tight

#### 10.9.
#    cuts.append(Cut('CR_WJets_noIDnorIso'       , inc_cut_relxd + l0_tight + noIDnorIso  + CR_WJets + '  &&  hnl_dr_12 < 0.4  &&  hnl_dr_hnvis0 > 1' + ZVeto01 + ZVeto02))
    cuts.append(Cut('CR_WJets_IDlNoIso'         , inc_cut_relxd + l0_tight + IDlNoIso    + CR_WJets + '  &&  hnl_dr_12 < 0.4  &&  hnl_dr_hnvis0 > 1' + ZVeto01 + ZVeto02))
#    cuts.append(Cut('CR_WJets_IDlIso15'         , inc_cut_relxd + l0_tight + IDlIso15    + CR_WJets + '  &&  hnl_dr_12 < 0.4  &&  hnl_dr_hnvis0 > 1' + ZVeto01 + ZVeto02))

    return cuts

def createSamples(analysis_dir, total_weight, qcd_from_same_sign, w_qcd_mssm_method, r_qcd_os_ss):
    hist_dict = {}
    sample_dict = {}
#    set_trace()
    samples_mc, samples_data, samples, all_samples, sampleDict = createSampleLists(analysis_dir=analysis_dir, channel = mode)
    
    sample_dict['all_samples'] = all_samples
#    sample_dict['samples_essential'] = samples_essential

    return sample_dict, hist_dict

def createVariables(rebin=None):
    # Taken from Variables.py; can get subset with e.g. getVars(['mt', 'mvis'])
    # variables = taumu_vars
    # variables = getVars(['_norm_', 'mt', 'mvis', 'l1_pt', 'l2_pt', 'l1_eta', 'l2_eta', 'n_vertices', 'n_jets', 'n_bjets'])
#    variables = CR_vars
    DoNotRebin = ['_norm_', 'n_vtx', 'nj', 'nbj',] 
    variables = hnl_vars
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
            plot.Group('Diboson', ['WZTo3LNu', 'ZZTo4L', 'WWTo2L2Nu'])
            plot.Group('Triboson', ['ZZZ', 'WWW', 'WGGJets'])
            plot.Group('ttV', ['TTZToLLNuNu', 'TTWJetsToLNu'])
            # plot.Group('DY', ['DYJets_M5T50', 'DYJets_M50_x', 'DYJets_M50'])
            plot.Group('DY', ['DYJetsToLL_M5to50', 'DYJets_ext'])
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
        

    mode = 'm'

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

    variables = createVariables(2)

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
