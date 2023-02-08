import http.server
import argparse
import rtspserver

def run(server_class=http.server.HTTPServer, handler_class=rtspserver.RTSPServer, addr="localhost", port=554):
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
