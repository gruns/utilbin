# -*- coding: utf-8 -*-

# Copyright _!_
#
# License _!_
#
# Original author: Ansgar Grunseid

# The code below is based off of, and modelered after, the code from
#
#   https://github.com/njsmith/h11/blob/master/examples/curio-server.py.
#
# See the comments and notes in that file for more information on gluing curio
# and h11 together for a simple HTTP server and the various gotchas and corner
# cases of the code below.
#
# TODO(grun): Expand this barebones HTTP server implementation into a
# standalone, independent HTTP server of h11+curio that can be extended and
# used independently of utilbin.

import h11
import curio

import traceback
from socket import SHUT_WR
from itertools import count
from wsgiref.handlers import format_date_time

DEFAULT_PORT = 9090
DEFAULT_TIMEOUT = 10  # Seconds.
DEFAULT_INTERFACE = ''
DEFAULT_MAX_RECEIVE_SIZE = 2 ** 16  # Bytes.

def callableAttr(obj, attr):
    return hasattr(obj, attr) and callable(getattr(obj, attr))


class PlainHTTPSocketWrapper:
    _connectionIterator = count()  # Unique int per connection. For debugging.

    def __init__(self, sock, maxRecvSize=None):
        self.sock = sock
        self.http = h11.Connection(h11.SERVER)
        self.uid = next(self._connectionIterator)
        self.maxRecvSize = maxRecvSize or DEFAULT_MAX_RECEIVE_SIZE
        h = h11.__version__
        c = curio.__version__
        self.serverName = f'plain-http-server curio:{c} h11:{h}'.encode('ascii')

    async def getNextEvent(self):
        while True:
            event = self.http.next_event()
            if event is h11.NEED_DATA:
                await self._readFromClient()
                continue
            return event

    async def send(self, event):
        # The code below doesn't send ConnectionClosed, so we don't bother
        # handling it here either -- it would require that we do something
        # appropriate when 'data' is None.
        data = self.http.send(event)
        await self.sock.sendall(data)

    async def sendTextResponse(self, statusCode, text):
        if callableAttr(text, 'encode'):  # String to bytes.
            text = text.encode('utf8')
        mimetype = 'text/plain; charset=utf-8'
        await self.sendSimpleResponse(statusCode, mimetype, text)

    async def sendSimpleResponse(self, statusCode, contentType, body):
        headers = self.createResponseHeaders(contentType, len(body))
        resp = h11.Response(status_code=statusCode, headers=headers)
        await self.send(resp)
        await self.send(h11.Data(data=body))
        await self.send(h11.EndOfMessage())

    async def sendExceptionResponse(self, exc):
        if self.http.our_state not in {h11.IDLE, h11.SEND_RESPONSE}:
            return

        try:
            statusCode = 500
            if isinstance(exc, h11.RemoteProtocolError):
                statusCode = exc.error_status_hint
            await self.sendTextResponse(statusCode, str(exc))
        except Exception as exc:
            print(f'Failed to send error response to client:')
            traceback.print_exception(None, exc, exc.__traceback__)

    async def handleRequest(self, req):
        await self.sendTextResponse(200, 'hi')

    async def closeConnection(self):
        # When this method is called, it's because we definitely want to kill
        # this connection, either as a clean shutdown or because of some kind
        # of error or loss-of-sync bug, and we no longer care if that violates
        # the protocol or not. So we ignore the state of self.http, and just go
        # ahead and do the shutdown on the socket directly. (If you're
        # implementing a client you might prefer to send ConnectionClosed() and
        # let it raise an exception if that violates the protocol.)
        #
        # Curio bug: doesn't expose shutdown()
        with self.sock.blocking() as real_sock:
            try:
                real_sock.shutdown(SHUT_WR)
            except OSError:
                return  # Connection already closed.

        # Wait and read for a bit to give them a chance to see that we closed
        # things, but eventually give up and just close the socket.
        # XX FIXME: possibly we should set SO_LINGER to 0 here, so
        # that in the case where the client has ignored our shutdown and
        # declined to initiate the close themselves, we do a violent shutdown
        # (RST) and avoid the TIME_WAIT?
        # it looks like nginx never does this for keepalive timeouts, and only
        # does it for regular timeouts (slow clients I guess?) if explicitly
        # enabled ("Default: reset_timedout_connection off")
        async with curio.ignore_after(TIMEOUT):
            try:
                while True:  # Attempt to read until end of the request.
                    ignored = await self.sock.recv(self.maxRecvSize)
                    if not ignored:
                        break
            finally:
                await self.sock.close()

    def createResponseHeaders(self, contentType='text/plain; charset=utf-8',
                              contentLength=None):
        headers = [
            ('Server', self.serverName),
            ('Content-Type', contentType),
            ('Date', format_date_time(None).encode('ascii')),
        ]
        if contentLength:
            headers.append(('Content-Length', str(contentLength)))
        return headers

    async def _readFromClient(self):
        if self.http.they_are_waiting_for_100_continue:
            headers = self.constructBasicHeaders()
            resp = h11.InformationalResponse(status_code=100, headers=headers)
            await self.send(resp)
        try:
            data = await self.sock.recv(self.maxRecvSize)
        except ConnectionError:
            data = b''  # Client closed the connection.
        self.http.receive_data(data)


class PlainHTTPServer:
    SocketWrapper = PlainHTTPSocketWrapper
    connectionTimeout = DEFAULT_TIMEOUT  # Seconds.
    maxReceiveSize = DEFAULT_MAX_RECEIVE_SIZE  # Bytes.

    def __init__(self, wrapper=None):
        self.SocketWrapper = wrapper or self.SocketWrapper

    def serveForever(self, interface='', port=None):
        port = port or DEFAULT_PORT
        interface = interface if interface is not None else DEFAULT_INTERFACE

        kernel = curio.Kernel()
        try:
            kernel.run(curio.tcp_server(interface, port, self.handleConnection))
        except KeyboardInterrupt:
            # Cancel all daemonic tasks and perform a clean shutdown once all
            # regular tasks have completed.
            print(
                'KeyboardInterrupt: Waiting for all non-daemonic '
                'tasks to finish...')
            kernel.run(shutdown=True)

    async def handleConnection(self, sock, addr):
        conn = self.SocketWrapper(sock, maxRecvSize=self.maxReceiveSize)

        while True:  # Process all requests on this connection.
            try:
                async with curio.timeout_after(self.connectionTimeout):
                    event = await conn.getNextEvent()
                    if type(event) is h11.Request:
                        req = event
                        await conn.handleRequest(req)
            except Exception as exc:
                print(f'Unhandled exception during response handler:')
                print(traceback.format_exc())
                await conn.sendExceptionResponse(exc)

            if conn.http.our_state is h11.MUST_CLOSE:
                await conn.closeConnection()
                break
            else:
                try:
                    conn.http.start_next_cycle()
                except h11.ProtocolError:
                    exc = RuntimeError(f'Unexpected HTTP state {conn.http.states}.')
                    await conn.sendExceptionResponse(exc)
                    await conn.closeConnection()
                    break
