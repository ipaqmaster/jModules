import os
import re

class XWindow():

    def __init__(self,target,debug=False):
        self.debug      = debug
        self.targetInfo = {}
        self.setTarget(target)

    def setTarget(self, target):
        """Set a new target"""
        self.target = target
        self.getTarget()

    def getTarget(self):
        """Get the window id of the desired target"""
        all_windows   = os.popen('xwininfo -tree -root').read()
        matches       = re.findall(f'^.*{self.target}.*$', all_windows, re.MULTILINE)

        if len(matches) == 0:
            print(f'No matches for a window text "{self.target}".')
            print('Please confirm the window is open and your string is accurate')
            exit(1)

        elif len(matches) > 1:
            print(f'Too many matches for window text "{self.target}". Please use a more specific target string.')
            print('')
            print(f'Matches:')
            print('\n'.join(matches))
            exit(1)
        else:
            self.targetWindowId = matches[0].split()[0] # Take the 0xWindowID only
            self.getTargetProperties()

    def getTargetProperties(self):
        """Get information about the target window"""

        # Process this information into key,values
        self.targetInfo = {}

        if not self.target:
            print('[getTargetProperties] Need target first!')
            return(False)

        self.targetInfo['id']          = self.targetWindowId

        # Use the ID to re-fetch cleaner info

        window_info = os.popen(f'xwininfo -id {self.targetInfo['id']}').read()


        for line in window_info.split('\n'):
            #print(line)
            if ':' in line:
                delimiter=':'
            else:
                delimiter=' '

            line = line.strip() # Remove prefixed whitespace
            line_split = line.split(delimiter)
            key        = line_split[0]
            value      = delimiter.join(line_split[1:]).strip()
            if key == '' or value == '':
                continue
            self.targetInfo[key]=value

        if 'Corners' in self.targetInfo:
            self.targetInfo['Corners'] = self.targetInfo['Corners'].strip().split('  ')

        self.targetInfo['dimensions']  = re.findall(r'\d+',self.targetWindowId[5])
        self.targetInfo['Center']      = [int(self.targetInfo['Width']) / 2, int(self.targetInfo['Height']) / 2]

        if self.debug:
            print('Got K,V\'s:')
            from pprint import pprint
            pprint(self.targetInfo, sort_dicts=False)

