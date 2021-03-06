#!/usr/bin/env python
"""
General plotting tool to plot SPEAD based correlator output
"""

import numpy, pylab, h5py, time, sys, math
import poxy

if __name__ == '__main__':
    from optparse import OptionParser
    o = OptionParser()
    o.set_usage('%prog [options] CONFIG_FILE')
    o.set_description(__doc__)
    o.add_option('-a', '--ant', dest='ant', default=None,
        help='For corrected data with a bl table select which antennas to plot, <ant_i> will plot all bls with that antenna, <ant_i>_<ant_j> will plot that baseline, auto: plot auto correlations')
    o.add_option('-c', dest='chan_index', default='all',
        help='Select which channels to plot. Options are <ch_i>,...,<ch_j>, or a range <ch_i>_<ch_j>. Default=all')
    o.add_option('-i', '--index', dest='bl_index', default=0,
        help='Select which baseline index. Options are <bl0>,...,<bln>, or a range <bl0>_<bln>. Default=0')
    o.add_option('-m', '--mode', dest='mode', default='lin',
        help='Plotting mode: lin, log, real, imag, phs. Default=log')
    o.add_option('-p', '--pol', dest='pol', default='all',
        help='Select which polarization to plot (xx,yy,xy,yx,all). Default=all')
    o.add_option('-t', '--time', dest='time', default=None, help='Select which time samples to plot, <t_i> or <t_i>,<t_j>,... or if in waterfall mode <t_0>_<t_k>. Default: all times')
    o.add_option('-w','--water', dest='water', default=False, action='store_true',
        help='Produce a waterfall plot of a time range using -t <t_0>_<t_n>')
    o.add_option('--chan', dest='chan_time', action='store_true',
        help='Plot individual channels as a function of time')
    o.add_option('--legend', dest='legend', action='store_true',
        help='Show a legend for every plot.')
    o.add_option('--share', dest='share', action='store_true',
        help='Share plots in a single frame.')
    opts, args = o.parse_args(sys.argv[1:])
    if args==[]:
        print 'Please specify a hdf5 file! \nExiting.'
        exit()
    else:
        fnames = args

def convert_arg_range(arg):
    """Split apart command-line lists/ranges into a list of numbers."""
    arg = arg.split(',')
    init = [map(int, option.split('_')) for option in arg]
    rv = []
    for i in init:
        if len(i) == 1:
            rv.append(i[0])
        elif len(i) == 2:
            rv.extend(range(i[0],i[1]+1))
    return rv

def convert_ant(arg,bl_order):
    """Return a list of baselines to plot"""
    arg = arg.split(',')
    rv = []
    if arg[0]=='all':
        for b,bl in enumerate(bl_order): rv.append(b)
    elif arg[0]=="auto":
        for b,bl in enumerate(bl_order):
            if bl[0]==bl[1]: rv.append(b)
    else:
        init = [map(int, option.split('_')) for option in arg]
        for i in init:
            if len(i) == 1:
                for b,bl in enumerate(bl_order):
                    if (i==bl[0]) | (i==bl[1]): rv.append(b)
            elif len(i) == 2:
                for b,bl in enumerate(bl_order):
                    if (i[0]==bl[0] and i[1]==bl[1]) | (i[1]==bl[0] and i[0]==bl[1]): rv.append(b)
    return rv

def tup_bls(bls):
    rv=[]
    for i,j in bls:
        rv.append((i,j))
    rv=tuple(rv)
    return rv

pol_map = {'xx':0,'yy':1,'xy':2,'yx':3}
map_pol = ['xx','yy','xy','yx']
def convert_pol(arg):
    """Parse polarization options"""
    if arg == 'all':
        return [pol_map['xx'], pol_map['yy'], pol_map['xy'], pol_map['yx']]
    else:
        arg = arg.split(',')
        rv = []
        for pi in arg: rv.append(pol_map[pi])
        return rv

bl_order=None


for fi, fname in enumerate(fnames):
    print "Opening:",fname, "(%d of %d)"%(fi+1,len(fnames))
    fh = h5py.File(fname, 'r')
    t = fh.get('timestamp0')
    if opts.time is None:
        time_index=range(len(t))
    else: time_index = convert_arg_range(opts.time)
    if fi==0:
        if 'pol' in fh.keys() and opts.pol.startswith('all'):
            unique_pols = list(numpy.unique(fh['pol']))
            pols = []
            for pi in unique_pols: pols.append(pol_map[pi])
        else: pols = convert_pol(opts.pol)
        
        if 'bl_order' in fh.keys() and opts.ant:
            bl_order = fh['bl_order'].value
            bl_index = convert_ant(opts.ant, bl_order)
            bl_order=tup_bls(bl_order)
        if not opts.ant:
            bl_index = convert_arg_range(opts.bl_index)
        
        #make the index list unique
        bl_index=numpy.unique(bl_index)
        
        m2 = int(math.sqrt(len(bl_index)))
        m1 = int(math.ceil(float(len(bl_index)) / m2))
        
        n_ants = fh.attrs.get('n_ants')
        if bl_order is None: bl_order = poxy.casper.get_bl_order(n_ants)
        if opts.chan_index == 'all': chan_index = range(0,fh.attrs.get('n_chans'))
        else: chan_index = convert_arg_range(opts.chan_index)
   
        #print fh['xeng_raw0'].shape
        #d = fh.get('xeng_raw0')[time_index]
        #if len(time_index) > len(chan_index):
        #    d = fh.get('xeng_raw0')[:,chan_index][time_index,:][:,:,bl_index][:,:,:,pols]
        #else: 
        #    d = fh.get('xeng_raw0')[time_index][:,chan_index][:,:,bl_index][:,:,:,pols]
        d = fh.get('xeng_raw0')[time_index][:,chan_index][:,:,bl_index][:,:,:,pols]
    #else: d = numpy.concatenate((d, fh.get('xeng_raw0')[time_index][chan_index][bl_index][pols]))
    else: d = numpy.concatenate((d, fh.get('xeng_raw0')[time_index][:,chan_index][:,:,bl_index][:,:,:,pols]))
    #print d.shape
    fh.flush()
    fh.close()

for cnt,bl in enumerate(bl_index):
    if not opts.share:
        pylab.subplot(m2, m1, cnt+1)
        dmin,dmax = None,None
    for pi in pols:
        #real: 1
        #imag: 0
        #di = numpy.vectorize(complex)(d[:,:,bl,pi,1], d[:,:,bl,pi,0])
        #di = d[:,:,bl,pi,1] + d[:,:,bl,pi,0]*1j
        di = d[:,:,cnt,pi,1] + d[:,:,cnt,pi,0]*1j
        #channel selection
        #di = di[:,chan_cnt]
        if opts.mode.startswith('lin'):
            di = numpy.absolute(di)
        if opts.mode.startswith('log'):
            di = numpy.absolute(di)
            di = numpy.log10(di)
        if opts.mode.startswith('real'): di = di.real
        if opts.mode.startswith('imag'): di = di.imag
        if opts.mode.startswith('ph'):
            di = numpy.angle(di)

        label = str(bl_order[bl]) + str(map_pol[pi])
        if not opts.share:
            if di.max()>dmax: dmax=di.max()
            if di.min()<dmin: dmin=di.max()
        print '.',
        sys.stdout.flush()
        if opts.water:
            pylab.imshow(di, aspect='auto')
            #pylab.pcolor(di)
        else:
            if opts.chan_time:
                for c in range(len(chan_index)):
                    pylab.plot(di[:,c])
                    pylab.ylim(-numpy.pi,numpy.pi)
            else:
                for t in range(len(time_index)):
                    #pylab.plot(di[t], '.', label=label)
                    pylab.plot(di[t], label=label)

    if not opts.share and not opts.water:
        pylab.ylim(dmin,dmax)
        pylab.title(bl_order[bl])

if opts.legend: pylab.legend()
if opts.water: pylab.colorbar()
print 'done'
pylab.show()

