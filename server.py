import http.server
import requests
import uuid
import argparse
import re
#from urllib3.util import SKIP_HEADER
import urllib3
from updatedrequesthandler import UpdatedRequestHandler
import threading
import socket
import io
import rtp_work
import time

# class SessionEntry :
#     def __init__( self ) :
#         self.session_id = 0
#         self.session_client = ()
#         self.

class S(UpdatedRequestHandler):

    def __init__( self, request, client_address, server ) :
        self.sessionList = {}
        super().__init__( request, client_address, server )
        #asdlkasd
        #qwiuoiqw

    #sessionList = {}

    # :_
    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    # remove later
    def _html(self, message):
        """This just generates an HTML document that includes `message`
        in the body. Override, or re-write this do do more interesting stuff.
        """
        content = f"<html><body><h1>{message}</h1></body></html>"
        return content.encode("utf8")  # NOTE: must return a bytes object!

    def do_SETUP(self):
        # если в свойствах есть сессия, то ругнуться по RFC
        # если нет, то создать новую и записать параметры клиента + target path?
        # если стрим, уже вещается, то сделать что? )
        # отправить ответ клиенту
        #print( f"setup, {self.headers}" )
        #print( self.protocol_version )
        #self._set_headers()
        #self.wfile.write(self._html("hi!"))
        #print( self.path )
        #print( self.requestline )
        #print( "setup" )
        #print( self.client_address )
        #print( self.headers )
        #
        if "Session" in self.headers :

            session = self.headers["Session"]
            sessionInfo = self.sessionList[session]

        else :

            # create sesstion ID and source socket
            session = uuid.uuid4().hex

            source_socket = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
            source_socket.bind( ( '', 0 ) )

            sessionInfo = { "session" : session, "client" : self.client_address, "source_socket" : source_socket }
            self.sessionList.update( { session : sessionInfo } )

        # update transport info
        transport = self.headers["Transport"]
        
        reg = re.search( "client_port=(\d+)-(?:\d+)", transport )
        if reg is None :
            self.send_response( 400, "Bad Client Port" )
            self.send_header( "CSeq", self.headers["CSeq"] )
            self.end_headers()
            return

        udp_port = int( reg.group( 1 ) )
        udp_address = self.client_address[0]

        sessionInfo["transport"] = transport
        sessionInfo["udp_address"] = udp_address
        sessionInfo["udp_port"] = udp_port

        # get source socket port
        ( _, source_port ) = sessionInfo["source_socket"].getsockname() 

        #
        #print( f"setup: session {session} for client {self.client_address}" )

        #
        self.send_response( 200 )
        self.send_header( "CSeq", self.headers["CSeq"] )
        self.send_header( "Public", "DESCRIBE, SETUP, TEARDOWN, PLAY, OPTIONS" )
        self.send_header( "Session", session )
        self.send_header( "Transport", transport + f";server_port={source_port}-{source_port+1}")
        self.end_headers()
        #

    def do_DESCRIBE( self ) :
        #self.notimplemented()
        #print( f"describe, {self.headers}" ) 
        #content = "m=video 96 H264/90000/704/576\r\nm=audio 0 PCMU/8000/1\r\n"
        sdp = [
            "m=video 0 RTP/AVP 96",
            "m=audio 0 RTP/AVP 0",
            "a=rtpmap:96 H264/90000/704/576"
        ]
        content = "\r\n".join( sdp ) + "\r\n"

        self.send_response( 200 )
        self.send_header( "CSeq", self.headers["CSeq"] )
        self.send_header( "Public", "DESCRIBE, SETUP, TEARDOWN, PLAY, OPTIONS" )
        self.send_header( "Content-Base", self.path )
        self.send_header( "Content-Type", "application/sdp" )
        self.send_header( "Content-Length", len( content ) )
        self.end_headers()

        self.wfile.write( content.encode( "ascii" ) )
        

    def readBytes( self, stream : io.BufferedIOBase, count ) :
        # create array
        result = bytes()
        #
        while len( result ) < count :
            data = stream.read( count - len( result ) )
            if data is None : 
                return None
            result = result + data
        #
        return result


    def sendRtp( self, raw_rtp, sessionInfo ) :
        # do not cache UDP as transport info can change ) overwise pack sending to separate class?
        udp_address = sessionInfo["udp_address"]
        udp_port = sessionInfo["udp_port"]
        #
        sessionInfo["source_socket"].sendto( raw_rtp, ( udp_address, udp_port ) )


    def processRtp( self, raw_rtp, sessionInfo ) :
        #
        rtp_headers  = rtp_work.DecodeRTPpacket( bytes.hex( raw_rtp ) ) # payload is HEXed bytes
        if rtp_headers["payload_type"] == 0 : # audio

            self.sendRtp( raw_rtp, sessionInfo )
            pass

        elif rtp_headers["payload_type"] == 96 : # video

            # chunk_size = 45000
            # # handle split ? 
            # # strip first two bytes (0x00000001 NAL prefix in byte0stream)
            # payload = bytes.fromhex( rtp_headers['payload'] )[4:]
            # chunk_start = 0
            # while chunk_start < len( payload ) :
            #     #
            #     payload_block = payload[chunk_start:chunk_start+chunk_size-1]
            #     chunk_start = chunk_start + chunk_size
            #     #
            #     rtp_headers['sequence_number'] = cseq_96
            #     cseq_96 = cseq_96 + 1
            #     rtp_data = bytes.fromhex( rtp_work.GenerateRTPpacket2( rtp_headers, bytes.hex( payload_block ) ) )
            #     targetSocket.sendto( rtp_data, ( udp_address, udp_port ) )
            #     time.sleep( 0.001 )
                #
            
            if len( raw_rtp ) < 65000 :
                rtp_payload = bytes.fromhex( rtp_headers['payload'] )[4:] # strip 4 bytes of NAL prefix
                rtp_data = bytes.fromhex( rtp_work.GenerateRTPpacket2( rtp_headers, bytes.hex( rtp_payload ) ) )
                self.sendRtp( rtp_data, sessionInfo )
                pass                            

# GET http://[IP]:[port]/livestream/[number]?action=play&media=[type] 
# HTTP/1.1\r\n 
# User-Agent: HiIpcam/V100R003 VodClient/1.0.0\r\n 
# Connection: Keep-Alive\r\n 
# Cache-Control: no-cache\r\n 
# Authorization: [username] [password] \r\n 
# Content-Length: [length] \r\n 
# \r\n 
# Cseq: 1\r\n 
# Transport: RTP/AVP/TCP;unicast;interleaved=0-1\r\n 
# \r\n 

    def playThread( self, sessionInfo ) :

        #
        headers = {
            'User-Agent' : 'HiIpcam/V100R003 VodClient/1.0.0',
            'Connection' : 'Keep-Alive',
            'Cache-Control' : 'no-cache',
            'Authorization' : 'ipcam w54723',
            #'Accept' : None,
            #'Accept-Encoding' : urllib3.util.SKIP_HEADER,
            #'Host' : urllib3.util.SKIP_HEADER
        }

        content = {
            'Cseq' : 1,
            'Transport' : 'RTP/AVP/TCP;unicast;interleaved=0-1'
        }
        raw_content = ("\r\n".join( key + ": " + str( content[key] ) for key in content ) + "\r\n").encode( "utf-8" )

        with requests.get( "http://192.168.1.77:80/livestream/11?action=play&media=video_audio_data", headers=headers, data=raw_content, stream=True ) as response :

            if response.status_code != 200 :
                print( f"domofon request {response.status_code}, {response.headers}" )
                return

            #
            tb = b''

            # skip headers
            while True :
                tb = self.readBytes( response.raw, 1 )
                if tb == b'$' : 
                    break

            if tb != b'$' :
                print( "initial $ not found" )
                return              

            #
            event = sessionInfo["thread_event"]
            #
            while tb == b'$' :

                if event.is_set() :
                    return

                # skip 3 bytes
                raw_channel_id = self.readBytes( response.raw, 1 )
                raw_reserve = self.readBytes( response.raw, 2 )

                # read length (int32, net-endianess)
                raw_length = self.readBytes( response.raw, 4 )
                length = int.from_bytes( raw_length, byteorder="big", signed=False )

                # read RTP packet
                raw_rtp = self.readBytes( response.raw, length )
                self.processRtp( raw_rtp, sessionInfo )

                # read next marker $
                tb = self.readBytes( response.raw, 1 )

            else :

                print( "non matching $ found" )


    def do_PLAY( self ) :
        # проверить пераметры session
        # если нет, то ругнуться по RFC
        # добавить эту сессию к списку слушателей для потока
        # запустить поток, если не запущен
        # сказать клиенту ок 
        session = self.headers["Session"]
        if session in self.sessionList :
            self.send_response( 200 )
            #
            sessionInfo = self.sessionList[session]
            # if not already playing
            if (not "thread" in sessionInfo) or (sessionInfo["thread"] is None) :
                # store threar for cleaning up?
                sessionInfo["thread"] = thread = threading.Thread( target=self.playThread, args=( sessionInfo, ), daemon=True )
                sessionInfo["thread_event"] = threading.Event()
                #
                thread.start()
        else :
            self.send_response( 404 )

        self.send_header( "CSeq", self.headers["CSeq"] )
        self.end_headers()

    #
    def do_TEARDOWN( self ) :
        # проверить session
        # елси нет, то ругнуться
        # если есть, то убрать сессию из списка слушателей
        # если это последний слушатель, то остановить поток
        # ответить клиенту
        session = self.headers["Session"]
        if session in self.sessionList :
            sessionInfo = self.sessionList.pop( session )
            sessionInfo["thread_event"].set()
            #
            sessionInfo["thread"] = None
            sessionInfo["thread_event"] = None
        #
        #print( f"teardown: session {session}" )
        self.send_response( 200 )
        self.send_header( "CSeq", self.headers["CSeq"] )
        self.end_headers()
        pass

    # def do_GET(self):
    #     self._set_headers()
    #     self.wfile.write(self._html("hi!"))

    def do_OPTIONS( self ) :
        #self.notimplemented()
        #print( f"options, {self.headers}" )
        #transport = self.headers["Transport"]
        self.send_response( 200 )
        self.send_header( "CSeq", self.headers["CSeq"] )
        self.send_header( "Public", "DESCRIBE, SETUP, TEARDOWN, PLAY, OPTIONS" )
        #self.send_header( "Session", session )
        #self.send_header( "Transport", transport + ";server_port=15678-15679")
        self.end_headers()

        #return
        # sliently ignore
        #print( "options" )
        #print( self.client_address )
        #print( self.headers )
        
    # def do_HEAD(self):
    #     self._set_headers()

    # def do_POST(self):
    #     # Doesn't do anything with posted data
    #     self._set_headers()
    #     self.wfile.write(self._html("POST!"))

    def notimplemented( self ) :
        print( self.command, "Not implemented" )
        self.send_response_only( 501, "Not implemented" )
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


def run(server_class=http.server.HTTPServer, handler_class=S, addr="localhost", port=554):
    server_address = (addr, port)
    print(f"Starting httpd server on {addr}:{port}")
    httpd = server_class(server_address, handler_class)
    try :
      httpd.serve_forever()
    except KeyboardInterrupt :
      httpd.server_close() 


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run a simple HTTP server")
    parser.add_argument(
        "-l",
        "--listen",
        default="0.0.0.0",
        help="Specify the IP address on which the server listens",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=554,
        help="Specify the port on which the server listens",
    )
    args = parser.parse_args()
    run(addr=args.listen, port=args.port)
