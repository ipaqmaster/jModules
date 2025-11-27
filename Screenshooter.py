from time import time
import subprocess
import sys

class Screenshooter():

    def __init__(self,windowId ,debug=False, loglevel=0):
        self.screenshot = None
        self.debug      = debug
        self.loglevel   = loglevel
        self.windowId   = windowId

        if self.debug:
            self.loglevel=7

    def getNextScreenshotPath(self, return_result=False):
        """For saving screenshots for debugging and further development without having to run the software or have a certain game state"""
        self.nowUnix        = time()
        self.outputDir      = 'tmp'
        self.outputFilename = 'screenshot.' + str(self.nowUnix) + '.png'
        self.screenshotPath = '%s/%s' % (self.outputDir,self.outputFilename)
        if return_result:
            return(self.screenshotPath)

    def get(self, return_result=False):
        #print('Taking screenshot') # Debug
        p = subprocess.Popen(['import', '-window', self.windowId,'PNG:-'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            self.stdout, self.stderr = p.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
            self.stdout, self.stderr = proc.communicate()

        if self.stdout:
            self.screenshot = self.stdout

        if self.debug:
            self.save()

        if return_result:
            return(self.screenshot)

    def save(self, Path=None):
        if not Path:
            self.getNextScreenshotPath()
            path = self.screenshotPath

        if self.screenshot and self.screenshotPath:
            try:
                with open(self.screenshotPath, "wb") as outputFile:
                    outputFile.write(self.screenshot)
                if self.loglevel >= 7: print('Saved: %s' % self.screenshotPath, file=sys.stderr)

                return(True)

            except Exception as e:
                print('Failed to save %s' % self.screenshotPath)
