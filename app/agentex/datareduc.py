'''
Citizen Science Portal: App containing Agent Exoplant and Show Me Stars for Las Cumbres Observatory Global Telescope Network
Copyright (C) 2014-2015 LCOGT

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

All non render/page based views are stored here, rather than views.py.
'''
from astropy.io import fits
from calendar import timegm
from datetime import datetime,timedelta
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.core.serializers import serialize
from django.db import connection
from django.db.models import Count, Avg, Min, Max, Variance, Q, Sum
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, render
from django.template import RequestContext

from django.urls import reverse
from itertools import chain
import numpy as np
from rest_framework.response import Response
from rest_framework import status
from time import mktime

from agentex.models import *
from agentex.forms import DataEntryForm, RegisterForm, CommentForm,RegistrationEditForm
import agentex.dataset as ds
from agentex.utils import achievementscheck

from django.conf import settings
from agentex.agentex_settings import planet_level

import logging

logger = logging.getLogger(__name__)

def personcheck(request):
    return request.user

def calibrator_data(calid,code):
    data = []
    sources, times = zip(*DataSource.objects.filter(event__name=code).values_list('id','timestamp').order_by('timestamp'))
    points  = Datapoint.objects.filter(data__in=sources)
    #points.filter(pointtype='C').values('data__id','user','value')
    people = Decision.objects.filter(source__id=calid,planet__name=code,value='D',current=True).values_list('person__username',flat=True).distinct()
    norm = dict((key,0) for key in sources)
    for pid in people:
        cal = []
        sc = dict(points.filter(user__username=pid,pointtype='S').values_list('data__id','value'))
        bg = dict(points.filter(user__username=pid,pointtype='B').values_list('data__id','value'))
        c = dict(points.filter(user__username=pid,pointtype='C',coorder__source__id=calid).values_list('data__id','value'))
        sc_norm = dict(norm.items() + sc.items())
        bg_norm = dict(norm.items() + bg.items())
        c_norm = dict(norm.items() + c.items())
        #print(sc_norm,bg_norm,c_norm)
        for v in sources:
            try:
                cal.append((sc_norm[v]- bg_norm[v])/(c_norm[v] - bg_norm[v]))
            except:
                cal.append(0)
        data.append(cal)
    return data,[timegm(s.timetuple())+1e-6*s.microsecond for s in times],list(people)

def average_combine(measurements,averages,ids,star,category,progress,admin=False):
    if progress['done'] < progress['total']:
        ave_measurement = averages.filter(star=star,settype=category)
        if ave_measurement.count() > 0:
            ## Find the array indices of my values and replace these averages
            ave = np.array(ave_measurement[0].data)
            mine = zip(*measurements.values_list('data','value'))
            try:
                my_ids = [ids.index(x) for x in mine[0]]
                ave[my_ids] = mine[1]
            except Exception as e:
                print(e)
            return ave
        else:
            return np.array([])
    elif progress['done'] == progress['total']:
        mine = np.array(measurements.values_list('value',flat=True))
        return mine
    elif not progress:
        print("No progress was passed")
        return np.array([])
    else:
        print("Error - too many measurements: %s %s" % (measurements.count() , numobs))
        return np.array([])

def calibrator_averages(code,person=None,progress=False):
    cals = []
    cats = []
    planet = Event.objects.get(name=code)
    sources = list(DataSource.objects.filter(event=planet).order_by('timestamp').values_list('id','timestamp'))
    ids,stamps = zip(*sources)
    if person:
        ## select calibrator stars used, excluding ones where ID == None, i.e. non-catalogue stars
        dc = DataCollection.objects.filter(~Q(source=None),person=person,planet=planet).order_by('calid')
        ## Measurement values only for selected 'person'
        dps = Datapoint.objects.filter(data__event=planet,user=person).order_by('data__timestamp')
    else:
        # select calibrator stars used, excluding ones where ID == None, i.e. non-catalogue stars
        dc = DataCollection.objects.filter(~Q(source=None),planet=planet).order_by('calid')
        ## Measurement values only for selected 'person'
        dps = Datapoint.objects.filter(data__event=planet).order_by('data__timestamp')
    averages = AverageSet.objects.filter(planet=planet)
    if person:
        # Make a combined list of source values
        measurements = dps.filter(pointtype='S')
        sc = average_combine(measurements,averages,ids,None,'S',progress)
        # Make a combined list of background values
        measurements = dps.filter(pointtype='B')
        bg = average_combine(measurements,averages,ids,None,'B',progress)
    else:
        sc = np.array(averages.filter(star=None,settype='S')[0].data)
        bg = np.array(averages.filter(star=None,settype='B')[0].data)
    # Make a combined list of all calibration stars used by 'person'
    for calibrator in dc:
        if person:
            measurements = dps.filter(pointtype='C',coorder=calibrator)
            ave = average_combine(measurements,averages,ids,calibrator.source,'C',progress)
        else:
            ave_cal = averages.filter(star=calibrator,settype='C')
            if ave_cal.count() > 0:
                ave = np.array(ave_cal[0].data)
            else:
                ave = np.array([])
        if ave.size > 0:
            cals.append(ave)
            try:
                if person:
                    decvalue = Decision.objects.filter(source=calibrator.source,person=person,planet=planet,current=True)[0].value
                else:
                    decvalue = Decision.objects.filter(source=calibrator.source, planet=planet,current=True)[0].value
            except:
                decvalue ='X'
            cat_item = {'sourcename':calibrator.source.name,'catalogue':calibrator.source.catalogue}
            cat_item['decsion'] = decvalue
            cat_item['order'] = str(calibrator.calid)
            cats.append(cat_item)
    return cals,sc,bg,stamps,ids,cats

def photometry(code,person,progress=False,admin=False):

    # Empty lists to store normalised calibrators and maximum values
    normcals = []
    maxvals = []
    dates = []
    stamps = []

    # Call in averages
    cals,sc,bg,times,ids,cats = calibrator_averages(code,person,progress)

    indexes = [int(i) for i in ids]
    #sc = np.array(sc)
    #bg = np.array(bg)

    # Iterate over every calibrator
    for cal in cals:
        if len(cal) == progress['total']:
            #### Do not attempt to do the photmetry where the number of calibrators does not match the total
                # Determine calibrated flux from source
                val = (sc - bg)/(cal-bg)
                # Determine maximum flux from source
                maxval = mean(r_[val[:3],val[-3:]])
                # Append to maxvals
                maxvals.append(maxval)
                # Normalise the maxval
                norm = val/maxval
                #Append the normalised value
                normcals.append(list(norm))
            # Find my data and create unix timestamps
        unixt = lambda x: timegm(x.timetuple())+1e-6*x.microsecond
        iso = lambda x: x.isoformat(" ")
        stamps = map(unixt,times)
        dates = map(iso,times)
    if admin:
        return normcals,stamps,indexes,cats
    return cals,normcals,list(sc),list(bg),dates,stamps,indexes,cats



def measure_offset(d,person,basiccoord):
    # Find the likely offset of this new calibrator compared to the basic ones and find any sources within 5 pixel radius search
    finderid = d.event.finder
    finderdp = Datapoint.objects.values_list('xpos','ypos').filter(user=person,data__id=finderid,pointtype='C',coorder__calid__lt=3).order_by('coorder__calid')
    finder = basiccoord - np.array(finderdp)
    t = np.transpose(finder)
    xmean = np.mean(t[0])
    ymean = np.mean(t[1])
    return xmean,ymean

def updatedisplay(request,code):
    # Wipe all the validations for user and event
    o = personcheck(request)
    dc = DataCollection.objects.filter(person=o.user,planet=Event.objects.get(name=code),complete=True)
    dc.update(display = False)
    empty = True
    formdata = request.POST
    for i,val in formdata.items():
        if i[4:] == val:
            # Add validations back one by one
            col = dc.filter(calid=val)
            col.update(display= True)
            empty = False
    return empty

def addvalidset(request,code):
    o = personcheck(request)
    calid = request.POST.get('calid','')
    choice1 = request.POST.get('choice1','')
    choice2 = request.POST.get('choice2','')
    point = DataCollection.objects.filter(person=o.user,calid=calid,planet__name=code)
    planet = Event.objects.filter(name=code)[0]
    if choice1 and point and calid:
        value = decisions[choice1]
        source = point[0].source
        old = Decision.objects.filter(person=o.user,planet=planet,source=source)
        old.delete()
        decision1 = Decision(source=source,
                        value=value,
                        person=o.user,
                        planet=planet)

        if choice2:
            value2 = decisions[choice2]
            decision2 = Decision(source=source,
                            value=value2,
                            person=o.user,
                            planet=planet,
                            current=True)
            decision2.save()
        else:
            decision1.current = True
        decision1.save()
        return False
    else:
        return True

@login_required
def my_data(o,code):
    data = []
    sources = DataSource.objects.filter(event__name=code).order_by('timestamp')
    points  = Datapoint.objects.filter(data__event__name=code,user=o.user)
    for s in sources:
        ps = points.filter(data=s)
        myp = ps.filter(pointtype='S')
        try:
            mypoint = '%f' % myp[0].value
        except:
            mypoint = 'null'
        cals = ps.filter(pointtype='C').values_list('value',flat=True).order_by('coorder')
        line = {
                'id'        : "%i" % s.id,
                'date'      : s.timestamp.isoformat(" "),
                'datestamp' : timegm(s.timestamp.timetuple())+1e-6*s.timestamp.microsecond,
                'data'      : { 'source' : list(ps.filter(pointtype='S').values_list('value',flat=True)),
                                'background' :  list(ps.filter(pointtype='B').values_list('value',flat=True)),
                                'calibrator' :  list(cals),
                            },
                }
        data.append(line)
    return data,points

def fitsanalyse(data):
    coords = list(zip(data['x'], data['y']))
    datasource = DataSource.objects.get(pk=data['id'])
    # Grab a fits file
    dfile = "%s%s" % (settings.DATA_LOCATION,datasource.fits)
    #logger.debug(dfile)
    dc = fits.getdata(dfile,header=False)
    r = datasource.event.radius
    linex = list()
    liney = list()
    counts = list()

    # Find all the pixels a radial distance r from x0,y0
    for co in coords:
        x0 = int(np.floor(co[0]))
        y0 = int(np.floor(co[1]))
        # Sum for this aperture
        sum = 0
        numpix = 0
        ys = y = y0 - r
        ye = y0 +r
        vline = list()
        hline = list()
        while (y < ye):
            angle = np.fabs(1.*(y-y0)/r)
            dx = int(np.sin(np.arccos(angle))*r)
            x = xs = x0 - dx
            xe = x0 + dx
            while (x < xe):
                sum += float(dc[y][x])
                x += 1
                if (x == x0):
                    hline.append(float(dc[y][x]))
                if (y == y0):
                    vline.append(float(dc[y][x]))
                    logger.debug("x = %s, y= %s val=%s" % (x,y,float(dc[y][x])))
                numpix += 1
            y += 1
        linex.append(hline)
        liney.append(vline)
        counts.append(sum)
    #logger.debug(datetime.now() - now)
    # Send back the raw total counts. Analysis can be done when the graph is produced.
    pointsum = {'bg' :  '%.2f' % counts[0], 'sc' : '%.2f' % counts[1], 'cal' : counts[2:]}
    lines = {'data' : {
               'coords' : {'xy' : coords,'r':r},
                'sum'   : pointsum,
                'points' : {'bg':
                                {'horiz' : linex[0],
                                'vert' : liney[0],
                                },
                            'sc':
                                {'horiz' : linex[1],
                                'vert' : liney[1],
                                },
                            'cal':
                                {'horiz' : linex[2:],
                                'vert' : liney[2:],
                                },
                            },
                #'quality' : flag,
               'pixelcount' : numpix,
                },
            }

    return lines

def savemeasurement(person, lines, dataid, mode):
    pointsum = lines['data']['sum']
    coordsxy = lines['data']['coords']
    # Only update the user's preference if they change it
    pointtype = {'sc':'S','bg':'B'}
    coords = list(coordsxy['xy']).copy()
    d = DataSource.objects.get(id=dataid)
    s_x = float(coords[1][0])
    s_y = float(coords[1][1])
    if d.id == d.event.finder:
        xvar = np.abs(s_x - d.event.xpos)
        yvar = np.abs(s_y - d.event.ypos)
        if (xvar > 3 or yvar > 3):
          # Remove previous values for this point
          return Response(data={'msg': 'Target marker not correctly aligned'}, status=status.HTTP_400_BAD_REQUEST)
    xmean = 0
    ymean = 0
    # Remove previous values for this point
    oldpoints = Datapoint.objects.filter(data=d,user=person)
    oldpoints.delete()
    numpoints = Datapoint.objects.filter(data__event=d.event,user=person).count()
    datestamp = datetime.now()
    reduced = 0
    calave = 0.
    error = ''
    ### Add a datacollection for the current user
    r = d.event.radius
    for k,value in pointtype.items():
        # Background and source
        data = Datapoint(ident=d.event.slug,
                            user=person,
                            pointtype = value,
                            data=d,
                            radius=r,
                            entrymode=mode,
                            tstamp=mktime(d.timestamp.timetuple())
                            )
        if k == 'sc':
            coord = coords[1]
            data.offset = 0
        elif k == 'bg':
            coord = coords[0]
            data.offset = int(np.sqrt((s_x - float(coord[0]))**2 + (s_y - float(coord[1]))**2))
        data.value= float(pointsum[k])
        data.xpos = int(float(coord[0]))
        data.ypos = int(float(coord[1]))
        data.taken=datestamp
        try:
            data.save()
        except:
            print("save error")
            return Response(data={'msg': 'Error saving data point'}, status=status.HTTP_400_BAD_REQUEST)
    # Slice coord data so we only have calibration stars
    coord = coords[2:]
    # Slice to get source and sky
    basiccoord = np.array(coords[:3])
    nocals = len(coord)
    sc_cal = float(pointsum['sc']) - float(pointsum['bg'])
    # Find out if means have been calculated already, if not do it for the source
    # This step can only happen if we are not at the finder frame
    if numpoints != 0 and d.event.finder != d.id:
        xmean, ymean = measure_offset(d,person,coord)
        # check the source is within this tolerance too
        sc_xpos = d.event.xpos
        sc_ypos = d.event.ypos
        xvar = np.abs(np.abs(sc_xpos-s_x)-np.abs(xmean))
        yvar = np.abs(np.abs(sc_ypos-s_y)-np.abs(ymean))
        if (xvar > 5 or yvar > 5):
            # Remove previous values for this point
            oldpoints = Datapoint.objects.filter(data__id=int(dataid),user=person)
            oldpoints.delete()
            return Response(data={'msg':'Markers not correctly aligned'}, status=status.HTTP_400_BAD_REQUEST)
    for i,value in enumerate(pointsum['cal']):
        xpos = int(float(coord[i][0]))
        ypos = int(float(coord[i][1]))
        newcoord = coord
        nocolls = DataCollection.objects.filter(planet=d.event,person=person,calid=i).count()
        if (nocolls == 0 and person != guestuser):
            ## Find closest catalogue sources
            if i > 2:
                # Add more datacollections if i is > 2 i.e. after basic 3 have been entered
                cats = CatSource.objects.filter(xpos__lt=xpos-xmean+5,ypos__lt=ypos-ymean+5,xpos__gt=xpos-xmean-5,ypos__gt=ypos-ymean-5,data__event=d.event)
            else:
                cats = CatSource.objects.filter(xpos__lt=xpos+5,ypos__lt=ypos+5,xpos__gt=xpos-5,ypos__gt=ypos-5,data__event=d.event)
            if cats:
                dcoll = DataCollection(person=person,planet=d.event,complete=False,calid=i,source=cats[0])
            else:
                dcoll = DataCollection(person=person,planet=d.event,complete=False,calid=i)
            dcoll.display = True
            dcoll.save()
        else:
            dcoll = DataCollection.objects.filter(person=person,planet=d.event,calid=i)[0]
        data = Datapoint(ident=d.event.slug,
                            user=person,
                            pointtype = 'C',
                            data=d,
                            radius=r,
                            entrymode='W',
                            tstamp=mktime(d.timestamp.timetuple())
                            )
        data.value= float(value)
        data.xpos = xpos
        data.ypos = ypos
        data.offset = int(np.sqrt((s_x - float(coord[i][0]))**2 + (s_y - float(coord[i][1]))**2))
        data.taken=datestamp
        data.coorder = dcoll
        try:
            data.save()
        except:
            return Response(data={'msg': 'Error saving'}, status=status.HTTP_400_BAD_REQUEST)
        calave = calave +sc_cal/(value - float(pointsum['bg']))/float(nocals)
    else:
        nomeas = Datapoint.objects.filter(user=person).values('taken').annotate(Count('taken')).count()
        noplanet = DataCollection.objects.filter(person=person).values('planet').annotate(Count('person')).count()
        ndecs = Decision.objects.filter(person=person,current=True).count() # filter: ,planet=d.event
        unlock = False
        nunlock = 0
        resp = achievementscheck(person,d.event,nomeas,noplanet,nocals,ndecs,0)
        msg = '<br />'
        for item in resp:
            if messages.SUCCESS == item['code'] :
                msg += "<img src=\""+settings.STATIC_URL+item['image']+"\" style=\"width:96px;height:96px;\" alt=\"Badge\" />"

        if resp:
            lines['msg'] = 'Achievement unlocked {}'.format(msg)
        else:
            lines['msg'] = 'Measurements saved'

        return Response(data=lines, status=status.HTTP_200_OK)

def datagen(slug,user):

    # Extract name of exoplanet from the dataset
    event = Event.objects.get(slug=slug)

    # Collect sources
    sources = DataSource.objects.filter(event=event).order_by('timestamp')

    numsuper,fz,mycals,std,nodata = supercaldata(user,event)

    data = []

    for i,s in enumerate(sources):
        line = {
                'id'        : "%i" % s.id,
                'date'      : s.timestamp.isoformat(" "),
                'datestamp' : timegm(s.timestamp.timetuple())+1e-6*s.timestamp.microsecond,
                'data'      : {
                                'mean' : fz[i],
                                'std'  : std[i],
                                'mine' : 'null',#myvals[i],
                    },
                }
        data.append(line)
    return data
