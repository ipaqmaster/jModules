import re

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

def printer(string=''):
    colorProcessing = False

    """A print wrapper which tries to add colors"""
    if type(string) == str:
      if '%' in string:
          colorEscapeScan = re.findall(r'%[a-zA-Z]+%', string)
          for colorEscape in colorEscapeScan:
              color = colorEscape.strip('%').lower()
              if color in colors:
                  string = string.replace(colorEscape, colors[color])
                  colorProcessing = True

    if colorProcessing:
        string = string + colors['none']
    print(string)
