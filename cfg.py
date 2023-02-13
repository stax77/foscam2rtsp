import configparser

_config = None

def readConfig( name="config.ini" ) :
    global _config
    _config = configparser.ConfigParser()
    _config.read( filenames=name )

def getConfig()  :
    global _config
    if _config is None :
        raise Exception( "Configuration not initialized" )
    return _config

def getStr( name, fallback=None ) :
    return getConfig().get( "default", name, fallback=fallback )

def getInt( name, fallback=None ) :
    return getConfig().getint( "default", name, fallback=fallback )
