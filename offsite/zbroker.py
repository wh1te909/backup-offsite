import zmq


def main():
    context = zmq.Context()
    frontend = context.socket(zmq.ROUTER)
    backend = context.socket(zmq.ROUTER)
    frontend.setsockopt(zmq.LINGER, 0)
    backend.setsockopt(zmq.LINGER, 0)
    frontend.bind("tcp://*:23957")
    backend.bind("tcp://*:23956")

    poller = zmq.Poller()
    poller.register(frontend, zmq.POLLIN)
    poller.register(backend, zmq.POLLIN)

    while 1:
        socks = dict(poller.poll())

        if socks.get(frontend) == zmq.POLLIN:
            message = frontend.recv_multipart()
            backend.send_multipart(message)

        if socks.get(backend) == zmq.POLLIN:
            message = backend.recv_multipart()
            frontend.send_multipart(message)

    frontend.close()
    backend.close()
    context.term()


if __name__ == "__main__":
    main()
