import os, imagehash
from PIL import Image

img1 = Image.new('RGB', (100, 100), color='red')
img1.save('img1.jpg')
ph1 = imagehash.phash(img1)
dh1 = imagehash.dhash(img1)

img4 = Image.new('RGB', (100, 100), color='red')
for x in range(10):
    for y in range(10):
        img4.putpixel((x,y), (0,0,0))
img4.save('img4.jpg')
ph4 = imagehash.phash(Image.open('img4.jpg'))
dh4 = imagehash.dhash(Image.open('img4.jpg'))

print(f"p1: {ph1}, d1: {dh1}")
print(f"p4: {ph4}, d4: {dh4}")
print(f"pdiff: {ph1 - ph4}, ddiff: {dh1 - dh4}")
