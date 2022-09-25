class Colors:
    """
    Dataclass with defined colors of the text written in console. To use it just write
    print(Colors.<name_of_color> + text + Colors.ENDC). Colors.ENDC is necessary if we want back to the original color
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
