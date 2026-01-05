import re
import sys

# An array of ANSI colors I like to use
colors =  {
  "none": "\033[0m",
  "red": "\033[31m",
  "green": "\033[32m",
  "yellow": "\033[33m",
  "blue": "\033[34m",
  "magenta": "\033[35m",
  "cyan": "\033[36m",
  "lightgray": "\033[37m",
  "white": "\033[97m"
}

def printer(message='', message_loglevel=0, loglevel=0, indent=0, end=None, logger=None):
    "A print wrapper which tries to add colors, indent and handle a loglevel"
    message_original    = message
    should_print        = None
    colorProcessing     = False

    indents = ' ' * 4 * indent
    file=sys.stdout

    # Skip printing if the log level is higher than the message
    if message_loglevel > loglevel:
        should_print = False
    else:
        should_print = True
        # Use stderr for any log level higher than 0
        if loglevel > 0:
            file=sys.stderr

    # Replace color placeholders with ANSI color escape sequences
    if type(message) == str:
        if '%' in message:
            colorEscapeScan = re.findall(r'%[a-zA-Z]+%', message)
            for colorEscape in colorEscapeScan:
                color = colorEscape.strip('%').lower()
                if color in colors:
                    message = message.replace(colorEscape, colors[color])
                    colorProcessing = True

    if colorProcessing:
        message = message + colors['none'] # Switch color back off at the end of any message.

    # Print
    print(message, end=None)

    # If logger is set, log too.
    if logger:
        logger(message_original)
