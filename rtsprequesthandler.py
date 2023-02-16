import re
import sessionmanager
import player
from basertsprequesthandler import BaseRTSPRequestHandler

class RTSPRequestHandler(BaseRTSPRequestHandler):

    # 
    def std_hdr( self ) :
        self.send_header( "CSeq", self.headers["CSeq"] )
        self.send_header( "Public", "DESCRIBE, SETUP, TEARDOWN, PLAY, OPTIONS" )

    #
    def do_SETUP( self ) :
        #
        #print( f"setup: {self.headers}" )
        # should check here for compatible transport RTP/AVP;unicast;client_port=, we dont support TCP or interleaved
        # extract transport data
        transport = self.headers["Transport"]
        # get client ports
        reg = re.search( "client_port=(\d+)-(?:\d+)", transport )
        if reg is None :
            self.send_response( 451, "Bad Client Port" )
            self.std_hdr()
            self.end_headers()
            return
        #
        target = ( self.client_address[0], int( reg.group( 1 ) ) )

        #extract stream type
        audio : bool = False
        if "stream=audio" in self.path :
            audio = True
        elif "stream=video" in self.path :
            audio = False
        else :
            self.send_response( 451, "Invalid stream option" )
            self.std_hdr()
            self.end_headers()
            return

        # extract session
        session = self.headers["Session"] if "Session" in self.headers else None
        session = sessionmanager.setup( session, target, audio )
        if session is None :
            self.send_response( 454, "Session not found" )
            self.std_hdr()
            self.end_headers()
            return

        # get source socket port
        ( _, source_port ) = player._socket.getsockname() 

        #
        self.send_response( 200 )
        self.std_hdr()
        self.send_header( "Session", session )
        self.send_header( "Transport", transport + f";server_port={source_port}-{source_port+1}")
        self.end_headers()

    #
    def do_DESCRIBE( self ) :
        #
        sdp = [
            # original pmap coming from intercom, incorrect
            # content = "m=video 96 H264/90000/704/576\r\nm=audio 0 PCMU/8000/1\r\n"
            # video map
            "m=video 0 RTP/AVP 96",
            "a=rtpmap: 96 H264/90000",
            "a=control:stream=video",
            # audio map
            "m=audio 0 RTP/AVP 0",
            "a=rtpmap: 0 PCMU/8000",
            "a=control:stream=audio",
            "\r\n"
        ]
        content = "\r\n".join( sdp ).encode( "ascii" )

        self.send_response( 200 )
        self.std_hdr()
        self.send_header( "Content-Base", self.path )
        self.send_header( "Content-Type", "application/sdp" )
        self.send_header( "Content-Length", len( content ) )
        self.end_headers()

        self.wfile.write( content )

    #
    def do_PLAY( self ) :
        session = self.headers["Session"]
        rtsp_status = 200 if sessionmanager.play( session ) else 454
        self.send_response( rtsp_status )
        self.std_hdr()
        self.end_headers()

    #
    def do_TEARDOWN( self ) :
        session = self.headers["Session"]
        rtsp_status = 200 if sessionmanager.teardown( session ) else 454
        self.send_response( rtsp_status )
        self.std_hdr()
        self.end_headers()

    #
    def do_OPTIONS( self ) :
        self.send_response( 200 )
        self.std_hdr()
        self.end_headers()

    def notimplemented( self ) :
        print( self.command, "Not implemented" )
        self.send_response( 501, "Not implemented" )
        self.std_hdr()
        self.end_headers()

    def do_ANNOUNCE( self ) :
        self.notimplemented()

    def do_GET_PARAMETER( self ) :
        self.notimplemented()

    def do_PAUSE( self ) :
        self.notimplemented()
    
    def do_SET_PARAMETER( self ) :
        self.notimplemented()

    def do_REDIRECT( self ) :
        self.notimplemented()

    def do_RECORD( self ) :
        self.notimplemented()

