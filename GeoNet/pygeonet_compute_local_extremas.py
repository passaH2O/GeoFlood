import numpy as np


def find_local_extremas(x):
    x = np.asarray(x)
    xmax = np.asarray([])
    imax = np.asarray([])
    xmin = np.asarray([])
    imin = np.asarray([])
    Nt = x.size
    if len(x) != max(x.shape):
        raise 'Entry must be a vector.'
    index_nan = np.argwhere(np.isnan(x))
    index = np.arange(len(x))
    if len(index_nan) != 0:
        index = index[~np.isnan(x)]
        x = x[~np.isnan(x)]
        Nt = x.size
    dx = np.diff(x)
    if not np.any(dx):
        print "This XS is an horizontal line"
        return [[0],[0],[0],[0]]
    a = np.array(np.where(dx!=0)).flatten()
    lm = np.array(np.where(np.diff(a)!=1)).flatten()
    if lm.size > 0:
        lm = lm+1
        d = a[lm] - a[lm-1]
        a[lm] = a[lm] - np.floor(d/2)
    a = np.append(a,Nt-1)
    xa = x[a]
    b = np.where(np.diff(xa)>0,1,0)
    xb = np.diff(b)
    imax = np.array(np.where(xb == -1)).flatten()
    if imax.size > 0:
        imax = imax+1
        imax = a[imax]
    imin = np.array(np.where(xb == 1)).flatten()
    if imax.size > 0:
        imin = imin+1
        imin = a[imin]
    nmaxi = imax.size
    nmini = imin.size
    if nmaxi == 0 and nmini == 0:
        if x[0] > x[-1]:
            xmax = [x[0]]
            imax = [index[0]]
            xmin = [x[-1]]
            imin = [index[-1]]
        elif x[0] < x[-1]:
            xmax = [x[-1]]
            imax = [index[-1]]
            xmin = [x[0]]
            imin = [index[0]]
        return [xmax,imax,xmin,imin]
    if nmaxi == 0:
        imax = [0,Nt-1]
    elif nmini == 0:
        imin = [0,Nt-1]
    else:
        if imax[0] < imin[0]:
            imin = np.insert(imin,0,0)
        else:
            imax = np.insert(imax,0,0)
        if imax[-1] > imin[-1]:
            imin = np.append(imin,Nt-1)
        else:
            imax = np.append(imax,Nt-1)
    xmax = x[imax]
    xmin = x[imin]
    if len(index_nan) != 0:
        imax = index[imax]
        imin = index[imin]
    imax = np.reshape(imax,xmax.shape)
    imin = np.reshape(imin,xmin.shape)
    inmax = np.argsort(-xmax)
    xmax = xmax[inmax]
    imax = imax[inmax]
    inmin = np.argsort(xmin)
    xmin = xmin[inmin]
    imin = imin[inmin]

    return [xmax,imax,xmin,imin]
        
