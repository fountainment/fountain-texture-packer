ftTexPac
========

A Python Texture Packer for Fountain game engine

Dependencies
------------

- Python 3.x
- Python Imaging Library(PIL)

How to use
----------

Try "python ftTexPacN.py PATH", PATH is the place where you put the images

Examples:

         $ python ftTexPacN.py ~/Documents/image
         $ python ftTexPacN.py ./image

Then you will get two files in your current working directory, one .png and one .ipi

.sip file
---------

sip represent for SubImagePool

The file contains info of packed images for Fountain game engine to read

Just use your text editor to view it, the format is simple

(become history)

.ipi file
---------

New file format to describe subimage

Includes anchor information

Tips
----

We may support other formats in future, like .plist for Cocos2d-x

Licence
-------

Licensed under the MIT License
