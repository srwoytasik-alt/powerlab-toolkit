def junction_temp_simple(Ta, P_total, Rth_ja):
    return Ta + P_total * Rth_ja

def junction_temp_detailed(Ta, P_total, Rth_jc, Rth_cs, Rth_sa):
    return Ta + P_total * (Rth_jc + Rth_cs + Rth_sa)

def safety_margin(Tj, Tj_max=150):
    return Tj_max - Tj
