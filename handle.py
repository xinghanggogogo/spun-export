#!/usr/bin/env pypy
# -*- coding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
#
# main script 
#

import sys
import re
import os

reload(sys)
sys.setdefaultencoding('utf-8')

# 查找歌词长度为30s左右
TIME_DUR = 20 
# 允许的误差,即假设最后一句歌词的长度
WC_DUR   = 5  
# 正则表达式模板
PATTAN = r'\[(\d*:[\d\.]*)\](.*)'

song_name = unicode(sys.argv[1], 'utf8')
print "\n\n>>>>>>>>>>>>>>>{%s}"%song_name

cnt = open(song_name).read()

def _get_time(time):
    m = re.match(r'(\d+):([\d\.]*)', time)
    return eval(m.group(1)) * 60 + eval(m.group(2))

def cmp_sort(x, y):
    ret = -cmp(x['count'], y['count'])
    if not ret:
        ret = cmp(x['times'][0], y['times'][0])
    return ret

def parse_lrc(song_name):

    lmp, lrc, mp = list(), list(), dict()

    for line in open(song_name):

        line = line.strip()
        if not line:
            continue
        match = re.match(PATTAN, line)
        if not match:
            continue

        times=[]
        times.append(match.groups()[0])
        line = match.groups()[1]
        match = re.match(PATTAN, line)
        while match:
            times.append(match.groups()[0])
            line = match.groups()[1]
            match = re.match(PATTAN, line)

        if line:
            if mp.has_key(line):
                mp[line]['count'] += len(times)
                mp[line]['times'] += times
            else:
                mp[line] = dict(count=len(times), times=times)
            mp[line]['times'].sort()

        #记录歌词顺序，空行也要保留
        for time in times:
            lrc.append(dict(lrc=line, time=time))

    for k, v in mp.items():
        data = v
        data.update({'lrc':k})
        lmp.append(data) 

    #排序方式：出现最多的句子并且出现的时间最早
    lmp.sort(cmp_sort)

    for line in lmp:
        print str(line['count']).rjust(5,'-'), line['times'][0].center(10,'_') ,line['lrc'].ljust(40,'_') 

    lrc.sort(lambda x, y: cmp(x['time'], y['time']))
    for one in lrc:
        print one['time'], one['lrc']

    return lmp, lrc

#在没有重复歌词的情况下，选取最后几句歌词
def get_tail(lrc):
    print "bad choice\n"

    gc = dict(start_time='', end_time='')
    end_time = lrc[len(lrc)-1]['time']
    gc['end_time'] = end_time
    sum  = WC_DUR if lrc[len(lrc) - 1]['lrc'] else 0
    last = _get_time(end_time)
    for i in xrange(len(lrc) - 2, -1, -1):
        one = lrc[i]
        now = _get_time(one['time'])
        sum = sum + last - now
        if sum >= TIME_DUR:
            gc['start_time'] = one['time']
            break
        last = now
    return gc

def get_popular(lmp, lrc):
    gc = dict(start_time='',end_time='')
    if not len(lmp): 
        return gc

    popular_line = lmp[0]
    last_line    = lrc[len(lrc) - 1]
    repeat_count = popular_line['count']

    #出现最多的句子不能没有重复的情况
    if repeat_count < 2:
        return get_tail(lrc)

    #选取中间偏后的句子,作为起始句
    idx        = int(repeat_count / 2)
    start_time = popular_line['times'][idx]
    end_time   = last_line['time'] + WC_DUR if last_line['lrc'] else last_line['time']

    #如果选取的起始时间过晚，以至于到结尾都不够所需的时间则调整起始时间
    if _get_time(start_time) + TIME_DUR > _get_time(end_time):
        if idx > 1:
            start_time = popular_line['times'][idx - 1]
            if _get_time(start_time) + TIME_DUR > _get_time(end_time):
                return get_tail(lrc)
        else:
            return get_tail(lrc)

    print '========================guess_most_popular========================================='
    print start_time,'\t' ,popular_line['lrc']

    gc['start_time'] = start_time
    sum, last = 0, _get_time(start_time)
    for one in lrc:
        if one['time'] > start_time:
            print one['time'], '\t', one['lrc']
            if sum >= TIME_DUR:
                gc['end_time'] = one['time']
                break
            now = _get_time(one['time'])
            sum = sum + now - last
            last = now

    if not gc['end_time']:
        gc['end_time'] = end_time

    return gc

def split_mp3(gc):
    if gc is None: 
        return

    start = _get_time(gc['start_time'])
    end   = _get_time(gc['end_time'])
    name = re.match(r'(.*).lrc$', song_name).group(1)
    cmd = 'ffmpeg -i "%s.mp3" -ss %s -t %s -acodec copy ./part/"%s.mp3"'%(name, start, end-start, name)
    print cmd
    os.system(cmd)

if __name__ == '__main__':
    lmp, lrc = parse_lrc(song_name)
    gc = get_popular(lmp, lrc)
    print gc
    # split_mp3(gc)
