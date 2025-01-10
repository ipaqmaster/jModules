#!/usr/bin/env python
from jModules.Colors     import colors,printer
from random              import randint
from time                import sleep

import colorsys
import cv2
import numpy as np
import os
import pytesseract
import random
import re
import signal
import string 
import subprocess
import time

_scriptRoot = os.path.dirname(os.path.realpath(__file__))
_scriptName = _scriptRoot.split('/')[-1]
_namespace  = _scriptName

class CV():
    def __init__(self, debug=False, loglevel=0, defaultMode='color', defaultThreshold=0.501):
        self.debug              = debug
        self.loglevel           = loglevel
        self.defaultMode        = defaultMode
        self.defaultThreshold   = defaultThreshold

        if self.debug:
            print('Debugging enabled. Loglevel set to 7')
            self.loglevel = 7

    def rgb_to_hsv(self,rgb):
        # Normalize our RGB values then convert them.
        normalized = (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
        hsv = colorsys.rgb_to_hsv(*normalized)

        # Scale HSV values to OpenCV ranges
        hsv = (int(hsv[0] * 180), int(hsv[1] * 255), int(hsv[2] * 255))

        return(list(hsv))

    def prepImage(self, image):
        """Takes a file path, bytes or an np.ndarray and returns a cv2 object via imread"""
        try:
            if isinstance(image, str):
                # Load the image
                image   = cv2.imread(image)
            elif isinstance(image, np.ndarray):
                image   = image
            elif isinstance(image, bytes):
                image   = np.asarray(bytearray(image), dtype="uint8")
                image   = cv2.imdecode(image, cv2.IMREAD_COLOR) # BGR
            else:
                printer('Unknown image format: %s' % type(image))
                exit()

        except Exception as e:
            printer('Failed to prepare an image: %s' % str(e))
            exit(1)

        return(image)

    def compareImages(self, image1, image2):
        """Compare two images for a similarity percentage in grayscale"""

        # Load the two images
        image1 = self.prepImage(image1)
        image2 = self.prepImage(image2)

        # Convert the images to grayscale
        gray_image1 = self.convertImage('gray',image1)
        gray_image2 = self.convertImage('gray',image2)

        # Compute Mean Squared Error (MSE) between them
        mse = ((gray_image1 - gray_image2) ** 2).mean()

        # use the MSE to gauge a percentage of similarity
        similarityPercentage = 100 - (mse / 255.0) * 100
        return(similarityPercentage)

    def getText(self, image, lang=None, mode=None, config=None, binaryMin=200, binaryMax=255):
        """Like getTextLocation but simply gets text from an image after processing."""

        image = self.prepImage(image)

        if mode:
            image = self.convertImage(mode, image, binaryMin=binaryMin, binaryMax=binaryMax)

        text = pytesseract.image_to_string(image, lang=lang, config=config)
        if text:
            return(text)
        else:
            return(False)


    def getTextLocation(self, xPercent, yPercent, xMax, yMax, image, lang=None, mode=None, config=None, binaryMin=200, binaryMax=255):
        """Get text from an image. Optionally provide a custom tesstrain dataset with lang='some-lang' from /usr/share/tessdata/."""

        image = self.prepImage(image)
        y, x, channels  = image.shape
        wFromPercentage, hFromPercentage = self.getCoordinatesFromPercentage(x, y, xPercent, yPercent)

        image = image[wFromPercentage:wFromPercentage+xMax, wFromPercentage:wFromPercentage+yMax]
        self.showImage(image)

        text = self.getText(image, lang=lang, mode=mode, config=config, binaryMin=binaryMin, binaryMax=binaryMax)
        if text:
            return(text)
        else:
            return(False)

    def showImage(self, imageData, results=None, annotate=False, title='image', timeout=1000):
        printer('showImage invoked...')
        if cv2.waitKey(timeout):
            cv2.destroyAllWindows()
        cv2.imshow(title, imageData)
        cv2.waitKey(timeout)
        cv2.destroyAllWindows()

    def searchImageInImage(self, needleImage, haystackImage, threshold=None, mode=None, cropX=None, cropY=None, cropLength=None, cropHeight=None):
        """Searches for an image inside another image with a strict default threshold."""
        """Accepts array of x,y,h,w for searching a cropped section of the haystack."""
        haystackImage_rgb = self.prepImage(haystackImage)
        needleImage_rgb   = self.prepImage(needleImage)

        if not threshold:
            threshold = self.defaultThreshold

        if not mode:
            mode      = self.defaultMode

        if self.debug: printer('Looking for %s' % os.path.basename(needleImage))


        # Get the dimensions of the needle image
        h, w = needleImage_rgb.shape[:2]


        # Crop the search area if requested.
        if cropX and cropY and cropLength and cropHeight:
            if self.debug: printer('Haystack is cropped.')
            haystackImage_rgb = haystackImage_rgb[cropY:cropY+cropHeight, cropX:cropX+cropLength]
            #self.showImage(haystackImage_rgb)

        # Match
        try:
            if mode == 'color':
                results             = cv2.matchTemplate(needleImage_rgb, haystackImage_rgb, cv2.TM_SQDIFF_NORMED)
            elif mode == 'grayscale':
                needleImage_gray    = self.convertImage('gray', needleImage_rgb)
                haystackImage_gray  = self.convertImage('gray', haystackImage_rgb)
                results             = cv2.matchTemplate(needleImage_gray, haystackImage_gray, cv2.TM_SQDIFF_NORMED)
            else:
                printer('Unknown mode %s' % mode)
        except Exception as e:
            print('Failed to compare:')
            print("\t%s" % haystackImage)
            print("\t%s" % needleImage)
            print(e)
            return(False)

        minVal, maxVal, minIdx, maxIdx = minMaxLoc = cv2.minMaxLoc(results)
        MPx, MPy = minIdx

        if self.debug:
            diff = abs(minVal - threshold)
            if minVal > threshold:
                state    = '%red%[Failed]%none%'
                position = 'over'
            else:
                state    = '%green%[Match]%none%\t'
                position = 'under'

            printer('\t%s Score: %s\t(Max: %s, %s by: %s)' % (state, minVal, threshold, position, diff))
            printer()

        if minVal >= float(threshold):
            #printer('Result greater than threshold (%s > %s)' % (minVal, threshold)) # Debug
            return(False)


        # Draw for debug
        #if self.debug:
        #    self.showImage(haystackImage_rgb)
        #    cv2.rectangle(haystackImage_rgb, (MPx, MPy), (MPx+w, MPy+h), (0, 0, 255) , 2)

        return(MPx, MPy, w, h)

    def getCoordinatesFromPercentage(self, x, y, xPercent, yPercent):
        xResult = int(x / 100 * xPercent)
        yResult = int(y / 100 * yPercent)
        return([xResult, yResult])

    def getPercentageFromCoordinates(self, x, y, sourceX=None, sourceY=None):
        xPercent = int(x / sourceX * 100)
        yPercent = int(y / sourceY * 100)
        return([xPercent, yPercent])

    def findBoxOfColorFilling(self, minHeight, minWidth, minColor, maxColor, image, maxHeight=None, maxWidth=None, mode='tall', multiple=False, convertToHSV=False, morphX=None, morphY=None):
        """Searches for boxes of a colored filling returning one or multiple results."""
        """By default looks for 'tall' rectangles."""
        """Could replace processScreenshot's text processing role by matching against white rectangles here instead."""
        """Can convert input R,G,B values to H,S,V"""

        image = self.prepImage(image)
        image_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        if convertToHSV:
            print('Ranges converted to HSV:')
            print('\t' , minColor, maxColor)
            minColor = np.array(self.rgb_to_hsv(minColor), np.uint8)
            maxColor = np.array(self.rgb_to_hsv(maxColor), np.uint8)
            print('After:')
            print('\t' , minColor, maxColor)
        else:
            print('Ranges kept as is:')
            print('\t' , minColor, maxColor)
            minColor = np.array(minColor)
            maxColor = np.array(maxColor)

        colorMask = cv2.inRange(image_hsv, minColor, maxColor)
        #self.showImage(colorMask, timeout=1000)

        # grow filtered image to fill gaps in the filtering.
        # Good for fixing up the gaps in the builder dropdown.
        if morphX and morphY:
            if self.debug: print('Morphing...')
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (morphX,morphY))
            colorMask = cv2.morphologyEx(colorMask, cv2.MORPH_DILATE, kernel)
            #self.showImage(colorMask, timeout=1000)

        contours, _ = cv2.findContours(colorMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print('contours: %s' % str(len(contours)))

        #if self.debug:
            #cv2.drawContours(image, contours, -1, (0, 255, 0), 2) # Debug draw
            #self.showImage(image, timeout=2000)


        if multiple:
            resultArray = []

        if contours:
            seenRectangles = [] # Avoid scanning the same match twice.

            for contour in contours:
                perimeter = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02*perimeter, True)
                x, y, w, h = cv2.boundingRect(approx)

                #if self.debug:
                #    print('Processing contour: %s' % str([x, y, w, h]))

                match mode:
                    case 'tall':
                        if w > h: # If not tall
                            continue

                    case 'wide':
                        if h > w: # If not wide
                            continue

                    case _:
                        printer('Unsupported mode.')
                        return(False)



                if [x, y, w, h] in seenRectangles:
                    #if self.debug: print('Rectangle already seen.')
                    continue

                if w < minWidth or h < minHeight:
                    #if self.debug: print('Min height or width not met.')
                    continue

                if maxHeight and maxWidth:
                    if h > maxHeight or w > maxWidth:
                        #if self.debug: print('Max height or width exceeded.')
                        continue

                if self.debug:
                    print("Height=%s, Width=%s" % (h, w))
                    print('Processing contour: %s' % str([x, y, w, h]))
                    #cv2.rectangle(image, (x, y), (x+w, y+h), (0, 0, 255) , 2); self.showImage(image, timeout=1000)

                seenRectangles.append([x, y, w, h])

                if multiple:
                    resultArray.append([x, y, w, h])

                else:
                    if self.debug: printer('Found a contour with filling')
                    return(x, y, w, h)

            if not multiple:
                return(False)

            if self.debug:
                printer('Found %d contours with filling' % len(resultArray))

            return(resultArray)

        else:
            if debug:
                print('Found no boxes of color filling.')
            return(False)

    def convertImage(self, mode, image, binaryMin=200, binaryMax=255):
        """A wrapper to quickly convert image data. On attempt failure returns the original image"""
        try:
            match mode:
                case 'gray':
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    return(gray)
                case 'binary':
                    _, binary = cv2.threshold(image, binaryMin, binaryMax, cv2.THRESH_BINARY)
                    return(binary)
                case 'invertedbinary':
                    _, invertedBinary = cv2.threshold(image, binaryMin, binaryMax, cv2.THRESH_BINARY_INV)
                    return(invertedBinary)
                case _: # Normal gameplay
                    printer('Not sure how to convert %s' % mode)
                    return(False)

        except Exception as e:
            #printer(str(e))
            return(image)

    def sortContours(self, contours, mode='top'):
        match mode:
            case 'x':
                return(sorted(contours, key=lambda ctr: cv2.boundingRect(ctr)[0]))
            case 'y':
                return(sorted(contours, key=lambda ctr: cv2.boundingRect(ctr)[1]))
            case _:
                printer('Not sure how to sort contours with a keyword like: %s' % mode)
                return(False)
