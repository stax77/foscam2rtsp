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
        #print( self.protocol_version )
        #self._set_headers()
        #self.wfile.write(self._html("hi!"))
        #print( self.path )
        #print( self.requestline )
        #print( "setup" )
        #print( self.client_address )
        #print( self.headers )
        #
        cseq = self.headers["CSeq"]
        if "Session" in self.headers :
            self.send_response( 459, "Aggregate Operation Not Allowed" )
            self.send_header( "CSeq", cseq )
            self.end_headers()
            return
        
        #
        session = uuid.uuid4().hex
        transport = self.headers["Transport"]
        
        #
        reg = re.search( "client_port=(\d+)-(?:\d+)", transport )
        if reg is None :
            self.send_response( 400, "Bad Client Port" )
            self.send_header( "CSeq", cseq )
            self.end_headers()
            return

        udp_port = int( reg.group( 1 ) )
        udp_address = self.client_address[0]

        #if self.sessionList is None :
        #    self.sessionList = {}
        sessionInfo = { "session" : session, "client" : self.client_address, "transport" : transport, "udp_address" : udp_address, "udp_port" : udp_port }
        self.sessionList.update( { session : sessionInfo } )

        #
        print( f"setup: new session {session} for client {self.client_address}" )

        #
        self.send_response( 200 )
        self.send_header( "CSeq", cseq )
        self.send_header( "Session", session )
        self.send_header( "Transport", transport ) # + ";server_port=15678-15679")
        self.end_headers()
        #

    def do_DESCRIBE( self ) :
        #self.notimplemented()

        content = "m=video 96 H264/90000/704/576\r\nm=audio 0 PCMU/8000/1\r\n"

        cseq = self.headers["CSeq"]
        self.send_response( 200 )
        self.send_header( "CSeq", cseq )
        self.send_header( "Content-Base", self.path )
        self.send_header( "Content-Type", "application/sdp" )
        self.send_header( "Content-Length", len( content ) )
        self.end_headers()

        self.wfile.write( content.encode( "ascii" ) )
        



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


    def playThread( self, udp_address, udp_port, event ) :

        #
        targetSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 

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

        # data = {
        #     'CSeq' : 1,
        #     'Transport' : 'RTP/AVP/TCP;unicast;interleaved=0-1'
        # }

        content = "Cseq: 1\r\nTransport: RTP/AVP/TCP;unicast;interleaved=0-1\r\n"
        raw_content = content.encode( "utf-8" )

        with requests.get( "http://192.168.1.77:80/livestream/11?action=play&media=video", headers=headers, data=raw_content, stream=True ) as response :
            #print( response )
            #print( response.headers )

            #response.iter_lines( )
            #hds = http.client.parse_headers( response.raw )
            #print( hds.keys() )

            #print( response.raw )

            #
            #for chunk in response.iter_content( chunk_size=1200 ) :
            #    targetSocket.sendto( chunk, ( udp_address, udp_port ) )

            # skip bytes till first $
            # add check for count )
            tb = b''

            while True :
                tb = self.readBytes( response.raw, 1 )
                if tb == b'$' : 
                    break

            if tb != b'$' :
                print( "initial $ not found" )
                return              

            #
            packet_num = 0
            cseq_96 = 0

            while tb == b'$' and not event.is_set() :

                # 
#                print( "$ found" )

                # skip 3 bytes
                raw_channel_id = self.readBytes( response.raw, 1 )
                raw_reserve = self.readBytes( response.raw, 2 )
                
                #

                # read length (int32, net-endianess)
                raw_length = self.readBytes( response.raw, 4 )
                # if len( raw_length ) != 4 :
                #     print( "failed to read 4 bytes!")
                #     return

                length = int.from_bytes( raw_length, byteorder="big", signed=False )

                #
                #print( f"packet {packet_num}, channe_id {raw_channel_id}, length {length}" )


                # read RTP packet
                raw_rtp = self.readBytes( response.raw, length )
                # if len( raw_rtp ) != length :
                #     print( f"failed to read {length} bytes!")
                #     return

                #
                rtp_headers  = rtp_work.DecodeRTPpacket( bytes.hex( raw_rtp ) ) # payload is HEXed bytes
                if rtp_headers["payload_type"] == 0 : # audio

                    targetSocket.sendto( raw_rtp, ( udp_address, udp_port ) )

                elif rtp_headers["payload_type"] == 96 : # video
                    chunk_size = 45000
                    # handle split ?
                    payload = bytes.fromhex( rtp_headers['payload'] )
                    if len( payload ) < chunk_size :
                        rtp_headers['sequence_number'] = cseq_96
                        cseq_96 = cseq_96 + 1
                        rtp_data = bytes.fromhex( rtp_work.GenerateRTPpacket2( rtp_headers, bytes.hex( payload ) ) )
                        targetSocket.sendto( rtp_data, ( udp_address, udp_port ) )
                    else :
                        chunk_start = 0
                        while chunk_start < len( payload ) :
                            #
                            payload_block = payload[chunk_start:chunk_size]
                            chunk_start = chunk_start + chunk_size
                            #
                            rtp_headers['sequence_number'] = cseq_96
                            cseq_96 = cseq_96 + 1
                            rtp_data = bytes.fromhex( rtp_work.GenerateRTPpacket2( rtp_headers, bytes.hex( payload_block ) ) )
                            targetSocket.sendto( rtp_data, ( udp_address, udp_port ) )
                            #
                            
                            

                #
                tb = self.readBytes( response.raw, 1 )
                packet_num = packet_num + 1

                #
            # checkbyte = response.iter_content( 1, False )
            # state = 0            
            # for byte in checkbyte :
            #     if state == 0 :
            #         if  byte == '$' :
            #             print( "symbol is ok" )
            #         state = 1
            #     elif state == 1 :
            #         #print( "not ok" )
            #         pass

            #response.raw

            print( "non matching $ found or thread break" )

            #response.iter_content( )


#        response.close()

        #pass

    def do_PLAY( self ) :
        # проверить пераметры session
        # если нет, то ругнуться по RFC
        # добавить эту сессию к списку слушателей для потока
        # запустить поток, если не запущен
        # сказать клиенту ок 
        #print( "play" )
        #print( self.client_address )
        #print( self.headers )

        cseq = self.headers["CSeq"]
        session = self.headers["Session"]
        #transport = self.headers["Transport"]

        if session in self.sessionList :
            self.send_response( 200 )
            #
            sessionInfo = self.sessionList[session]
            event = threading.Event()
            thread = threading.Thread( target=self.playThread, args=( sessionInfo["udp_address"], sessionInfo["udp_port"], event ), daemon=True )
            thread.start()
            # store threar for cleaning up?
            sessionInfo["thread"] = thread
            sessionInfo["thread_event"] = event
        else :
            self.send_response( 404 )

        self.send_header( "CSeq", cseq )
        self.end_headers()

    #
    def do_TEARDOWN( self ) :
        # проверить session
        # елси нет, то ругнуться
        # если есть, то убрать сессию из списка слушателей
        # если это последний слушатель, то остановить поток
        # ответить клиенту
        #print( "teardown" )
        #print( self.client_address )
        #print( self.headers )
        cseq = self.headers["CSeq"]
        session = self.headers["Session"]
        #
        if session in self.sessionList :
            sessionInfo = self.sessionList.pop( session )
            sessionInfo["thread_event"].set()
        #
        print( f"teardown: session {session}" )
        #transport = self.headers["Transport"]
        self.send_response( 200 )
        self.send_header( "CSeq", cseq )
        #self.send_header( "Session", session )
        #self.send_header( "Transport", transport + ";server_port=15678-15679")
        self.end_headers()
        pass

    # def do_GET(self):
    #     self._set_headers()
    #     self.wfile.write(self._html("hi!"))

    def do_OPTIONS( self ) :
        self.notimplemented()
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


def run(server_class=http.server.HTTPServer, handler_class=S, addr="localhost", port=8000):
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
        default="localhost",
        help="Specify the IP address on which the server listens",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Specify the port on which the server listens",
    )
    args = parser.parse_args()
    run(addr=args.listen, port=args.port)
