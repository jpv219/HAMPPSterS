import logging

# Config the logger, sets output file, level, and format
logging.basicConfig(
    filename="output.txt",
    level=logging.INFO,

    # format sets what the log message should include (time, level, message, etc)
    format="%(asctime)s - %(message)s",  
    
    # format the datetime's appearance
    datefmt="[%d/%m/ - %H:%M:%S]"
)


log = logging.getLogger(__name__)
