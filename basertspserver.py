import http.server
import sys

class BaseRTSPServer( http.server.HTTPServer ) :

    def handle_error(self, request, client_address):
        """Handle an error gracefully.  May be overridden.

        The default is to print a traceback and continue.

        """
#        print('-'*40, file=sys.stderr)
        print('Exception occurred during processing of request from', client_address, file=sys.stderr )
 #       import traceback
 #       traceback.print_exc()
 #       print('-'*40, file=sys.stderr)
    