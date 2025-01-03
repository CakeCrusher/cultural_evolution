# function to sanitize a string to be used as a filename remove colons and other special characters
def sanitize_filename(filename: str) -> str:
    return filename.replace(":", "_").replace("-", "_").replace(" ", "_")
