import logging

def configure_logger(name):
    logging.basicConfig(
        filename=f"{name}_output.txt",
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="[%d/%m/ - %H:%M:%S]"
    )

    logger = logging.getLogger(name)
    return logger
