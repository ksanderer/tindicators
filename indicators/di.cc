/*
 * This file is part of tindicators, licensed under GNU LGPL v3.
 * Author: Ilya Pikulin <ilya.pikulin@gmail.com>, 2019, 2021
 * Author: Lewis Van Winkle <lv@codeplea.com>, 2016-2017
 */


#include <new>

#include "../indicators.h"
#include "dx.h"


int ti_di_start(TI_REAL const *options) {
    return (int)options[0]-1;
}


int ti_di(int size, TI_REAL const *const *inputs, TI_REAL const *options, TI_REAL *const *outputs) {
    const TI_REAL *high = inputs[0];
    const TI_REAL *low = inputs[1];
    const TI_REAL *close = inputs[2];

    const int period = (int)options[0];

    TI_REAL *plus_di = outputs[0];
    TI_REAL *minus_di = outputs[1];

    if (period < 1) return TI_INVALID_OPTION;
    if (size <= ti_di_start(options)) return TI_OKAY;

    const TI_REAL per = ((TI_REAL)period-1) / ((TI_REAL)period);

    TI_REAL atr = 0;
    TI_REAL dmup = 0;
    TI_REAL dmdown = 0;

    int i;
    for (i = 1; i < period && i < size; ++i) {
        TI_REAL truerange;
        CALC_TRUERANGE();
        atr += truerange;

        TI_REAL dp, dm;
        CALC_DIRECTION(dp, dm);

        dmup += dp;
        dmdown += dm;
    }


    if (i == period) {
        *plus_di++  = dmup ? 100.0 * dmup / atr : 0;
        *minus_di++ = dmdown ? 100.0 * dmdown / atr : 0;
    }

    for (i = period; i < size; ++i) {
        TI_REAL truerange;
        CALC_TRUERANGE();
        atr = atr * per + truerange;


        TI_REAL dp, dm;
        CALC_DIRECTION(dp, dm);


        dmup = dmup * per + dp;
        dmdown = dmdown * per + dm;

        *plus_di++  = dmup ? 100.0 * dmup / atr : 0;
        *minus_di++ = dmdown ? 100.0 * dmdown / atr : 0;
    }


    assert(plus_di - outputs[0] == size - ti_di_start(options));
    assert(minus_di - outputs[1] == size - ti_di_start(options));

    return TI_OKAY;
}
