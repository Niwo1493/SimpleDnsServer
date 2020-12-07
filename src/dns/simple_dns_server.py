# std libraries
from sys import argv
from time import sleep
# local libraries
from connection_argument_extractor import ConnectionArgumentExtractor
from request_server import RequestServer
from dns.resource_record.resource_record_manager import ResourceRecordManager


class SimpleDnsServer:
    """
    A DNS server, which handles all incoming DNS lookup request.
    The class only support a very simple version of DNS requests.
    It will load it's resource records from a zone file,
    which must be passed initially as well as the ip address.
    The run() method can be used to start the server.
    The handle_request() method will be called for incoming requests
    to process them.
    """

    def __init__(self, zone_file: str, ip_address: str, port: int = 53053):
        self.record_manager = ResourceRecordManager.from_file(zone_file)
        self.ip_address = ip_address
        self.port = port
        self._ensure_connection_information()
        self.server = RequestServer(
            self.ip_address, self.port,
            self.handle_request, log_requests=True
        )  # TODO: Deactivate logging later.

    def run(self, in_background: bool = True) -> None:
        """
        Opens the socket and starts receiving requests.
        Will only return after KeyboardInterrupt.
        """
        self.record_manager.log_entries()
        self.server.open_socket()
        self.server.run()  # will be in background
        if not in_background:
            self.run_till_interrupt()

    def handle_request(self, request: str) -> str:
        """
        Called to handle a request.
        Should find the ip address of the domain.
        :param request: The received request as string, containing the domain.
        :return: The response to answer the client.
        """
        record = self.record_manager.get_match(request)
        # TODO: handle the actual request
        return "\r\n".join((
            "HTTP/1.1 200 OK",
            "",
            record.value if record is not None else '404'
        ))

    def stop_listening(self) -> None:
        """
        Stops listening for requests.
        The socket won't be removed.
        """
        self.server.stop_listening()

    def run_till_interrupt(self) -> None:
        while True:
            try:
                sleep(60)
            except KeyboardInterrupt:  # Ctrl + C
                print("Processing stopped, socket will remain blocked.")
                break
        self.stop_listening()

    def _ensure_connection_information(self) -> None:
        if type(self.port) == str and self.port.isnumeric():
            self.port = int(self.port)
        assert type(self.ip_address) == str and len(self.ip_address) >= 7, \
            "Ip address missing."
        assert type(self.port) == int, "Port must be numeric."


def started_as_main() -> bool:
    return __name__ == "__main__"


if started_as_main():
    arg_ip, arg_port = ConnectionArgumentExtractor(argv).get_arguments()
    dns_server = SimpleDnsServer(
        "../../rsrc/zone_files/root.zone",
        arg_ip, arg_port
    )
    dns_server.run(in_background=False)
