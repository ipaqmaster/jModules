#!/usr/bin/env python
from time import time
import datetime
import os
import sys

class Logger():

    def __init__(self, name=None, logDir=None, logFile=None, quiet=False, debug=False, loglevel=2):
        """
        A logging class.
        Name,           A name to put in the log lines for identification, by default the script's root directory name.
        quiet,          Hides logPrefix from prints
        logDir,         The logging directory - by default the script's location
        logFile,        A log filename, by default it's the name of the directory the sc ript is in + '.log'
        logFile=False   Disable log file
        debug,          Additional logging
        """

        self.loglevels      = ('info', 'warn', 'error', '4', '5', '6', '7', 'debug')
        self._scriptRoot    = _scriptRoot = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self._scriptName    = os.path.basename(self._scriptRoot)

        self.quiet   = quiet
        self.debug   = debug
        self.name    = name    or self._scriptName
        self.logDir  = logDir  or self._scriptRoot

        if logDir:
            if not os.path.isdir(logDir):
                print('[Logger] logDir does not exist: {logDir}')
                exit(1)

        if logFile is False:
            self.logFile = False
        elif logFile is None:
            self.logFile = logFile or f'{self._scriptName}.log' 
        elif type(logFile) is str:
            self.logFile = logFile or f'{self._scriptName}.log' 
        else:
            print(f'[Logger] Not sure how to handle logFile: {logFile}')
            exit(1) # Could add support for a descriptor later

        self.logPath = '%s/%s' % (self.logDir, self.logFile)

        print(f'[Logger] Logging to file: {self.logFile}')
        self.set_loglevel(loglevel)

    def set_loglevel(self, loglevel: int):
        self.loglevel = loglevel
        if self.debug:
            print(f'Log level set to {self.loglevel}')

    def log(self, text=None, loglevel=0, name=None, end=None, indent=0):
        """Log something and to a file with a default log level of 0 (info) where not specified."""

        # Determine an indentation if specified
        tabs      = '\t' * indent

        if not hasattr(self, 'timestamp'):
            self.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %T')

        if not hasattr(self, 'last_timestamp'):
            self.last_timestamp = time()
        else:
            if self.last_timestamp - time() > 1:
                print(self.last_timestamp - time())
            self.timestamp = datetime.datetime.now().strftime('%Y-%m-%d %T')

        #  Accept a custom name prefix on the log line
        if name:
            name  = name
        else:
            name  = self.name

        # Nothing? Print a newline
        if not text:
            text = '\n'

        # Log each line
        for line in text.splitlines():

            if self.quiet and not self.debug:
                logText = line
            else:
                logPrefix = '[%s] [%s] %s ' % (self.timestamp, name, f'[{self.loglevels[loglevel]}]'.ljust(8))
                logText = logPrefix + line

            # If we're at or above the required loglevel.
            # Print it
            if loglevel <= self.loglevel:
                if loglevel > 0:
                    file = sys.stderr
                else:
                    file = sys.stdout
                

                print(f'{tabs}{logText}', file=sys.stdout, end=end)

                # Log it (This seems inefficient...)
                if self.logFile:
                    with open(self.logPath, 'a') as file:
                        file.write(logText + '\n')
