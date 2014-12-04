#!/usr/bin/python

import sys, os, math
import PIL.Image as Image

MAX_PIC_NUM = 2000
MAX_TARGET_SIZE = 4096
INF = MAX_TARGET_SIZE * 2

typeFilter = ['png', 'jpg', 'jpeg', 'gif', 'bmp', '']
## you can add more to this typeFilter, as long as the PIL support it
## this typeFilter is to help dealing with files faster

def goThrough(rootDir):
    ans = []
    walkList = os.walk(rootDir)
    root, dirs, files = walkList.next() 
    for f in files:
        suffix = f.split('.')[-1]
        if suffix.lower() in typeFilter:
            ans.append((os.path.join(root, f), f))
    return ans

def picCmp(picA, picB):
    nameA, imA = picA
    nameB, imB = picB
    for i in range(2):
        if imA.size[i] != imB.size[i]:
            return cmp(imB.size[i], imA.size[i])
    return cmp(nameA, nameB)

if len(sys.argv) != 2:
    print('usage: ftTexPac.py [PATH]')
    exit(0)

path = sys.argv[1]

if not os.path.isdir(path):
    print('error: ' + path + ' is not a path!')
    exit(0)

picPathList = goThrough(path)
picList = []

for picPath, name in picPathList:
    isPic = True
    try:
        im = Image.open(picPath)
    except IOError:
        isPic = False
    if isPic:
        picList.append((name, im))

picList.sort(picCmp)
picN = len(picList)

if picN == 0:
    print('there is no pic in ' + path + '!')
    exit(0)

for name, im in picList:
    print('%-50s %5s %5dx%-5d' % (name, im.format, im.size[0], im.size[1]) + im.mode)

use = [0] * MAX_PIC_NUM
pxH = [0] * MAX_TARGET_SIZE
locList = [(0, 0)] * MAX_PIC_NUM

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
    global use
    global locList
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
    global pxH
    fillHeight = INF
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
    global use
    global pxH
    use = [0] * MAX_PIC_NUM
    pxH = [0] * MAX_TARGET_SIZE
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

maxLen = 0
for pic in picList:
    if pic[1].size[0] > maxLen:
        maxLen = pic[1].size[0]
    if pic[1].size[1] > maxLen:
        maxLen = pic[1].size[1]

minPower = int(math.log(maxLen) / math.log(2))
maxPower = int(math.log(MAX_TARGET_SIZE) / math.log(2))

find = False
for i in range(minPower, maxPower):
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
    print('find it!')
    bgcolor = (255, 255, 255, 0)
    outImage = Image.new('RGBA', (width, height), bgcolor)
    for i in range(picN):
        outImage.paste(picList[i][1], locList[i])
    absPath = os.path.abspath(path)
    splitPath = os.path.split(absPath)
    outName = splitPath[-1]
    if len(outName) == 0:
        outName = os.path.split(splitPath[-2])[-1]
    if len(outName) == 0:
        outName = 'noname'
    outImage.save(outName + '.png')
    ## sip represent for Sub Image Pool
    ## it is a file format for Fountain game engine
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
    print('sorry, not find a solution.')
