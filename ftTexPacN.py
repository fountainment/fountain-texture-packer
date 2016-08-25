#!/usr/bin/env python

import sys, os, math
import Queue
import PIL.Image as Image
from psd_tools import PSDImage, Layer, Group

def imageCmp(imA, imB):
    sa, sb = imA['size'], imB['size']
    na, nb = imA['name'], imB['name']
    if sa[0] != sb[0]:
        return cmp(sb[0], sa[0])
    if sa[1] != sb[1]:
        return cmp(sb[1], sa[1])
    return cmp(na, nb)

def nameCmp(imA, imB):
    na, nb = imA['name'], imB['name']
    na = ("%03d" % len(na)) + na
    nb = ("%03d" % len(nb)) + nb
    return cmp(na, nb)

def log2(n):
    return math.log(n) / math.log(2)

def isTransp(pixel):
    return pixel[3] == 0.0

def isBlue(pixel):
    return pixel == (0.0, 0.0, 1.0)

def getBox(image):
    pl = list(image.getdata())
    datasize = len(pl[0])
    if datasize == 3:
        jfunc = isBlue
    elif datasize == 4:
        jfunc = isTransp
    else:
        return (0, 0) + image.size
    sz = image.size
    l, b, r, t = sz[0], sz[1], 0, 0
    for y in range(sz[1]):
        minx, maxx = sz[0], 0
        emptyRow = True
        for x in range(sz[0]):
            if not jfunc(pl[y * sz[0] + x]):
                minx = min(minx, x)
                maxx = max(maxx, x)
                emptyRow = False
        if not emptyRow:
            b = min(y, b)
            t = max(y, t)
        l = min(minx, l)
        r = max(maxx, r)
    r += 1
    t += 1
    if r < l:
        r = l
    if t < b:
        t = b
    return (l, b, r, t)

def getGapInfo(pixelUse):
    gapH = float('inf')
    gapX = 0
    gapL = 0
    width = len(pixelUse)
    for i in range(width):
        if pixelUse[i] < gapH:
            gapX = i
            gapH = pixelUse[i]
    for i in range(gapX, width):
        if pixelUse[i] == gapH:
            gapL += 1
        else:
            break
    return (gapH, gapX, gapL)

def killGap(pixelUse, gapX, gapL):
    width = len(pixelUse)
    fillHeight = float('inf')
    if gapX - 1 >= 0:
        fillHeight = min(fillHeight, pixelUse[gapX - 1])
    if gapX + gapL < width:
        fillHeight = min(fillHeight, pixelUse[gapX + gapL])
    for i in range(gapX, gapX + gapL):
        pixelUse[i] = fillHeight

class TexPac:

    def __init__(self):

        #packing arguments
        self.__typeFilter = ['', 'png', 'jpg', 'jpeg', 'gif', 'bmp']
        self.__maxPackSize = 2048
        self.__inf = self.__maxPackSize * 2
        self.__reservedBlank = (0, 0)
        self.__reservedOuterBlank = (1, 1)
        self.__reservedPath = None
        self.__reservePath = False
        self.__cutBlank = True

        #runtime values
        self.__imagelist = []

        #output arguments
        self.__outImageList = []
        self.__outSize = (0, 0)
        self.__outName = None
        self.__outInfo = None
        self.__outFolder = None

    def packPathsInPath(self, path):
        walkList = os.walk(path)
        paths = []
        for i in walkList:
            root, dirs, files = i
            for d in dirs:
                paths.append(os.path.join(root, d))
        self.packPaths(paths)

    def packPaths(self, pathlist):
        for path in pathlist:
            print(path)
            self.packPath(path)
            print('')

    def packPath(self, path):
        if self.__outName == None:
            self.__outName = os.path.split(os.path.abspath(path))[-1]
            if len(self.__outName) == 0:
                self.__outName = 'noname'
        filelist = []
        walkList = os.walk(path)
        root, dirs, files = walkList.next()
        for f in files:
            suffix = f.split('.')[-1]
            if suffix.lower() in self.__typeFilter:
                filelist.append(f)
        self.__setReservedPath(os.path.split(path)[0])
        self.packFiles(root, filelist)

    def packPsd(self, psdfile):
        self.__getImageListFromPsd(psdfile)
        self.__pack()
        self.__clear()

    def packFiles(self, root, filelist):
        if len(filelist) == 0:
            print('error: ' + 'no pic to pack!')
            return

        self.__getImageList(root, filelist)
        self.__pack()
        self.__clear()

    def setReservedBlank(self, reservedBlank):
        self.__reservedBlank = reservedBlank

    def setReservedOuterBlank(self, reservedOuterBlank):
        self.__reservedOuterBlank = reservedOuterBlank

    def setMaxPackSize(self, maxPackSize):
        self.__maxPackSize = maxPackSize
        self.__inf = maxPackSize * 2

    def setOutputName(self, outname):
        self.__outName = outname

    def setOutputFolder(self, outfolder):
        self.__outFolder = outfolder

    def setReservePath(self, reservePath):
        self.__reservePath = reservePath

    def __setReservedPath(self, reservedPath):
        self.__reservedPath = reservedPath

    def __getImageList(self, root, filelist):
        self.__imagelist = []
        for f in filelist:
            imagepath = os.path.join(root, f)
            try:
                im = Image.open(imagepath)
            except IOError:
                continue
            self.__imagelist.append({'name': f, 'im': im, 'size': im.size, 'pos': (0, 0), 'anchor': (0.0, 0.0)})

    def __getImageListFromPsd(self, psdfile):
        psd = PSDImage.load(psdfile)
        psdsize = (psd.header.width, psd.header.height)
        layer_queue = Queue.Queue(maxsize = 2000)
        index = 0
        for layer in psd.layers:
            layer_queue.put(layer)
        while not layer_queue.empty():
            t = layer_queue.get()
            if t.visible and type(t) == Group:
                for layer in t.layers:
                    layer_queue.put(layer)
            elif t.visible and type(t) == Layer:
                im = t.as_PIL()
                loc = ((t.bbox.x1 + t.bbox.x2 - psdsize[0]) * 0.5, (t.bbox.y1 + t.bbox.y2 - psdsize[1]) * 0.5)
                self.__imagelist.append({'name': '%d' % index, 'im': im, 'size': im.size, 'pos': (0, 0), 'anchor': (-loc[0], -loc[1])})
                index += 1

    def __pack(self):
        if self.__cutBlank:
            self.__cutImageBlank()
        self.__sortImageList()
        find = self.__findSolution()

        if find:
            self.__output()
        else:
            print('error: no solution!')

    def __cutImageBlank(self):
        for image in self.__imagelist:
            box = getBox(image['im'])
            boxsize = (box[2] - box[0], box[3] - box[1])
            originsize = image['size']
            image['im'] = image['im'].crop(box)
            image['size'] = boxsize
            rb = self.__reservedBlank
            if rb != (0, 0):
                newBoxsize = (boxsize[0] + rb[0] * 2, boxsize[1] + rb[1] * 2)
                newImage = Image.new('RGBA', newBoxsize, (0, 0, 0, 0))
                newImage.paste(image['im'], rb)
                image['im'] = newImage
                image['size'] = newBoxsize
            image['anchor'] = ((originsize[0] - box[0] - box[2]) * 0.5 + image['anchor'][0], (originsize[1] - box[1] - box[3]) * 0.5 + image['anchor'][1])

    def __sortImageList(self):
        self.__imagelist.sort(imageCmp)

    def __trySolution(self, width, height):
        imageNum = len(self.__imagelist)
        imageUse = [0] * imageNum
        pixelUse = [0] * width
        curImage = 0
        gapH, gapX, gapL = getGapInfo(pixelUse)
        rob = self.__reservedOuterBlank
        while True:
            if curImage >= imageNum:
                break
            if imageUse[curImage] == 1:
                curImage += 1
                continue
            imageW = self.__imagelist[curImage]['size'][0] + rob[0] * 2
            imageH = self.__imagelist[curImage]['size'][1] + rob[1] * 2
            if gapL >= imageW:
                if gapH + imageH <= height:
                    for i in range(gapX, gapX + imageW):
                        pixelUse[i] += imageH
                    self.__imagelist[curImage]['pos'] = (gapX + rob[0], gapH + rob[1])
                    gapH, gapX, gapL = getGapInfo(pixelUse) 
                    imageUse[curImage] = 1
                    curImage += 1
                else:
                    return False
            else:
                if (gapL >= width) or (gapH >= height):
                    return False
                gapCanFill = False
                for imageI in range(curImage + 1, imageNum):
                    imageW = self.__imagelist[curImage]['size'][0] + rob[0] * 2
                    imageH = self.__imagelist[curImage]['size'][1] + rob[1] * 2
                    if (imageUse[imageI] == 0) and (gapL >= imageW):
                        if gapH + imageH <= height:
                            for i in range(gapX, gapX + imageW):
                                pixelUse[i] += imageH
                            self.__imagelist[imageI]['pos'] = (gapX + rob[0], gapH + rob[1])
                            gapH, gapX, gapL = getGapInfo(pixelUse)
                            imageUse[imageI] = 1
                            gapCanFill = True
                            break
                        else:
                            return False
                if not gapCanFill:
                    killGap(pixelUse, gapX, gapL)
                    gapH, gapX, gapL = getGapInfo(pixelUse)
        return True

    def __findSolution(self):
        sizeSum = 0
        maxWidth = 0
        for image in self.__imagelist:
            name = image['name']
            im = image['im']
            w, h = image['size']
            anchor = image['anchor']
            print('%-30s %4dx%-4d %4s (%.1f, %.1f)' % ((name, w, h, im.mode) + (anchor[0], anchor[1])))
            sizeSum += w * h
            maxWidth = max(maxWidth, w)
        minPower = int(log2(max(maxWidth, int(math.sqrt(sizeSum)))))
        maxPower = int(log2(self.__maxPackSize))
        for i in range(minPower, maxPower + 1):
            s = 2**i
            if self.__trySolution(s, s):
                self.__outSize = (s, s)
                return True
            if self.__trySolution(s * 2, s):
                self.__outSize = (s * 2, s)
                return True
        return False

    def __output(self):
        bgcolor = (0, 0, 0, 0)
        outImage = Image.new('RGBA', self.__outSize, bgcolor)
        filePath = ""
        if self.__outFolder != None:
            filePath = self.__outFolder
        if self.__reservePath == True and self.__reservedPath != None:
            filePath = os.path.join(filePath, self.__reservedPath)
        if not os.path.exists(filePath):
            os.makedirs(filePath)
        fileName = os.path.join(filePath, self.__outName)
        for image in self.__imagelist:
            outImage.paste(image['im'], image['pos'])
        outImage.save(fileName + '.png')

        imageNum = len(self.__imagelist)
        outFile = open(fileName + '.ipi', 'w')
        outFile.write('%d %d\n' % self.__outSize)
        outFile.write('%d\n' % imageNum)
        outInfo = []
        self.__imagelist.sort(nameCmp)
        for image in self.__imagelist:
            name = image['name']
            size = image['size']
            pos = image['pos']
            anchor = image['anchor']
            outInfo.append('%s %d %d %d %d %.1f %.1f\n' % ((name,) + size + pos + anchor))
        outFile.writelines(outInfo)
        outFile.close()

    def __clear(self):
        self.__imagelist = []
        self.__outImageList = []
        self.__outSize = (0, 0)
        self.__outName = None
        self.__outInfo = None
        self.__reservedPath = None

def packAll(path):
    packer = TexPac()
    packer.setOutputFolder('output')
    packer.setReservePath(True)
    packer.packPathsInPath(path)

def main():
    argn = len(sys.argv)

    if argn != 2 and argn != 3:
        print('usage: ftTexPac.py [FOLDER/PSDFILE] [OUTPUTNAME]')
        return

    packType = ''
    if os.path.isdir(sys.argv[1]):
        packType = 'folder'
    elif os.path.isfile(sys.argv[1]):
        packType = 'psdfile'
    else:
        print('error: ' + sys.argv[1] + ' is neigher a folder or a psd file!')
        return

    path = os.path.abspath(sys.argv[1])

    if argn == 3:
        outname = sys.argv[2]
    else:
        outname = os.path.split(path)[-1]
        if outname[-4:] == '.psd':
            outname = outname[:-4]
    if len(outname) == 0:
        outname = 'noname'

    packer = TexPac()
    packer.setMaxPackSize(4096)
    packer.setReservedBlank((0, 0))
    packer.setReservedOuterBlank((1, 1))
    packer.setOutputName(outname)
    if packType == 'folder':
        packer.packPath(path)
    elif packType == 'psdfile':
        packer.packPsd(path)

if __name__ == '__main__':
    main()
