import basertspserver
import argparse
import rtsprequesthandler
import cfg

def run( server_class=basertspserver.BaseRTSPServer, handler_class=rtsprequesthandler.RTSPRequestHandler, addr="localhost", port=554 ):
    server_address = (addr, port)
    print(f"Starting RTSP server on {addr}:{port}")
    httpd = server_class( server_address, handler_class )
    try :
      httpd.serve_forever()
    except KeyboardInterrupt :
      pass

if __name__ == "__main__":

    parser = argparse.ArgumentParser( description="Run a simple RTSP converter :)" )
    # parser.add_argument(
    #     "-l",
    #     "--listen",
    #     default="0.0.0.0",
    #     help="Specify the IP address on which the server listens",
    # )
    # parser.add_argument(
    #     "-p",
    #     "--port",
    #     type=int,
    #     default=554,
    #     help="Specify the port on which the server listens",
    # )
    # run( addr=args.listen, port=args.port )

    parser.add_argument( "-i", "--ini", type=str, default="config.ini", help="Path of .ini file" )
    args = parser.parse_args()

    #
    cfg.readConfig( args.ini )

    #
    server_port = cfg.getInt( "port" )
    server_address = cfg.getStr( "address" )
    run( addr=server_address, port=server_port )
