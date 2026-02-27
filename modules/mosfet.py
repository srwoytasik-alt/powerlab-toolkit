import numpy as np

def conduction_loss(I_rms, Rds_on):
    return I_rms**2 * Rds_on

def switching_loss(Vds, Id, tr, tf, f_sw):
    return 0.5 * Vds * Id * (tr + tf) * f_sw

def total_loss(P_cond, P_sw):
    return P_cond + P_sw
