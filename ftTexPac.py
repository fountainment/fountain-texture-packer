#!/usr/bin/python

import sys, os, commands
import PIL.Image as Image

def goThrough(rootDir): 
    ans = []
    root, dirs, files = os.walk(rootDir).next() 
    for f in files:
        ans.append((os.path.join(root, f), f))
    return ans

if len(sys.argv) != 2:
    print 'usage: texturePacker pathname'
    exit(0)

path = sys.argv[1]

if not os.path.isdir(path):
    print 'error: ' + path + 'is not a path!'
    exit(0)

piclist = goThrough(path)
picList = []

for picPath, name in piclist:
    isPic = True
    try:
        im = Image.open(picPath)
    except IOError:
        isPic = False
    if isPic:
        picList.append((name, im))

def picCmp(picA, picB):
    nameA, imA = picA
    nameB, imB = picB
    for i in range(2):
        if imA.size[i] != imB.size[i]:
            return cmp(imB.size[i], imA.size[i])
    return cmp(nameA, nameB)

picList.sort(picCmp)
picN = len(picList)
for name, im in picList:
    print "%-50s %5s %5dx%-5d" % (name, im.format, im.size[0], im.size[1]), im.mode

if picN == 0:
    print 'there is no pic in ' + path + '!'
    exit(0)

global pxH
global use
global minH
global minX
global minL
global width
global height
global locList

use = [0] * 1000
pxH = [0] * 4096
locList = [(0, 0)] * 1000

def getMinHXL():
    global minH
    global minX
    global minL
    minX = 0
    minH = height + 1
    minL = 0
    for i in range(width):
        if pxH[i] < minH:
            minX = i
            minH = pxH[i]
    for i in range(minX, width):
        if pxH[i] == minH:
            minL += 1
        else:
            break

def place(index, x, y):
    use[index] = 1
    locList[index] = (x, y)
    for i in range(picList[index][1].size[0]):
        if x + i >= width:
            break
        pxH[x + i] += picList[index][1].size[1]
        if pxH[x + i] > height:
            return False
    getMinHXL()
    return True

def killGap(x):
    fillHeight = 2000000
    if x - 1 >= 0:
        if pxH[x - 1] < fillHeight:
            fillHeight = pxH[x - 1]
    if x + minL < width:
        if pxH[x + minL] < fillHeight:
            fillHeight = pxH[x + minL]
    for i in range(x, x + minL):
        pxH[i] = fillHeight
    getMinHXL()
    	

def work():
    global minH
    global minX
    global minL
    global pxH
    global use
    use = [0] * 1000
    pxH = [0] * 4096
    cur = 0
    getMinHXL()
    while True:
        if cur >= picN:
            break
        if (use[cur] == 0) and (minL >= picList[cur][1].size[0]):
            tmp = place(cur, minX, minH)
            if not tmp:
                return False
        else:
            if use[cur] == 1:
                cur += 1
                continue
            if (minL == width) or (minH > height):
                return False
            gapCanFill = False
            for fill in range(cur + 1, picN):
                if (use[fill] == 0) and (minL >= picList[fill][1].size[0]):
                    tmp = place(fill, minX, minH)
                    if not tmp:
                        return False
                    gapCanFill = True
                    break
            if not gapCanFill:
                killGap(minX)
            continue
        cur += 1
    ss = 0
    for i in range(picN):
        ss += use[i]
    if ss == picN:
        return True
    else:
        return False

find = False
for i in range(5, 12):
    t = 2**i
    width = t
    height = t
    if work():
        find = True
        break
    width = t / 2
    height = t * 2
    if work():
        find = True
        break
    width = t * 2
    height = t
    if work():
        find = True
        break
    width = t
    height = t * 2
    if work():
        find = True
        break

if find:
    print 'find it!'
    bgcolor = (255, 255, 255, 0)
    outImage = Image.new('RGBA', (width, height), bgcolor)
    for i in range(picN):
        outImage.paste(picList[i][1], locList[i])
    outName = os.path.split(path)[-1]
    if len(outName) == 0:
        outName = os.path.split(path)[-2]
    if cmp(outName, '.') == 0:
        outName = 'pwd'
    outImage.save(outName + '.png')
    #sip represent for Sub Image Pool
    #it is a file format for Fountain game engine
    outFile = open(outName + '.sip', 'w')
    outFile.write('%d %d\n' % (width, height))
    outFile.write('%d\n' % picN)
    outInfo = []
    for i in range(picN):
        name, im = picList[i]
        size = im.size
        pos = locList[i]
        outInfo.append('%s %d %d %d %d\n' % (name, size[0], size[1], pos[0], pos[1]))
    outFile.writelines(outInfo)
    outFile.close()
else:
    print 'sorry, not find a solution.'
