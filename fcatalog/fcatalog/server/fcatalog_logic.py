import asyncio
import logging
import os
import string

from fcatalog.proto.msg_endpoint import MsgEndpoint
from fcatalog.server.fcatalog_proto import cser_serializer,FSimilar
from fcatalog.funcs_db import FuncsDB

class ServerLogicError(Exception): pass


# Set up logger:
logger = logging.getLogger(__name__)

def is_good_db_name(db_name):
    """
    Check if a db_name is valid. We have to be careful of directory traversal
    here.
    """
    good_chars = string.ascii_letters + string.digits + "_"
    for c in db_name:
        if c not in good_chars:
            return False

    return True


class FCatalogServerLogic:
    def __init__(self,db_base_path,num_hashes,msg_endpoint):
        # Keep database base path:
        self._db_base_path = db_base_path
        # Keep amount of hashes:
        self._num_hashes = num_hashes
        # Message endpoint:
        self._msg_endpoint = msg_endpoint

        # Initially Functions Database interface is None:
        self._fdb = None

    @asyncio.coroutine
    def client_handler(self):
        """
        Main logic of the catalog1 server, for one client.
        Communication with the client is done through the msg_endpoint class
        instance.
        """
        logger.debug('New connection {}'.format(id(self._msg_endpoint)))
        msg_inst = ( yield from self._msg_endpoint.recv() )

        if msg_inst is None:
            # Remote peer has disconnected or sent invalid data. We disconnect.
            logger.debug('Remote peer has disconnected or sent invalid data')
            return

        logger.debug('Connection has message: {}'.format(msg_inst.msg_name))

        if msg_inst.msg_name != 'ChooseDB':
            # If the first message is not ChooseDB, we disconnect.
            logger.debug('Connection {} has {} as first message.'
                    ' Closing connection.'.\
                            format(msg_inst.msg_name, id(self._msg_endpoint)))
            return

        # Database name:
        db_name = msg_inst.get_field('db_name')

        # Validate database name:
        if not is_good_db_name(db_name):
            logger.info('Invalid db name {} was chosen at connection {}'.\
                    format(db_name,id(self._msg_endpoint)))
            # Disconnect the client:
            return

        # Conclude database path:
        db_path = os.path.join(self._db_base_path,db_name)

        logger.debug('db_path = {} at connection {}'.\
                format(db_path,id(self._msg_endpoint)))

        # Build a Functions DB interface:
        self._fdb = FuncsDB(db_path,self._num_hashes)
        try:
            msg_inst = ( yield from self._msg_endpoint.recv() )
            while msg_inst is not None:
                if msg_inst.msg_name == 'ChooseDB':
                    # We can't have two ChooseDB messages in a connection. We
                    # close the connection:
                    return
                elif msg_inst.msg_name == 'AddFunction':
                    yield from self._handle_add_function(msg_inst)
                elif msg_inst.msg_name == 'AddStructure':
                    yield from self._handle_add_structure(msg_inst)
                elif msg_inst.msg_name == 'RequestSimilars':
                    yield from self._handle_request_similars(msg_inst)
                elif msg_inst.msg_name == 'RequestStructNames':
                    yield from self._handle_request_struct_names(msg_inst)
                elif msg_inst.msg_name == 'RequestFuncNames':
                    yield from self._handle_request_func_names(msg_inst)
                elif msg_inst.msg_name == 'SYN':
                    yield from self._handle_SYN(msg_inst)
                elif msg_inst.msg_name == 'RequestStruct':
                    yield from self._handle_request_struct(msg_inst)
                else:
                    # This should never happen:
                    raise ServerLogicError('Unknown message name {}'.\
                            format(msg_inst.msg_name))

                # Receive the next message:
                msg_inst = ( yield from self._msg_endpoint.recv() )

            logger.debug('Received a None message on connection {}'.\
                    format(id(self._msg_endpoint)))

        finally:
            # We make sure to eventually close the fdb interface (To commit all
            # changes that might be pending).
            self._fdb.close()

    @asyncio.coroutine
    def _handle_SYN(self, msg_inst):
        logger.debug("Handle SYN")
        resp_msg = cser_serializer.get_msg('ACK')
        yield from self._msg_endpoint.send(resp_msg)

    @asyncio.coroutine
    def _handle_add_structure(self, msg_inst):
        struct_name = msg_inst.get_field('struct_name')
        struct_dump = msg_inst.get_field('struct_value')
        logger.debug('AddStructure: struct_name={}'.\
                format(struct_name))

        self._fdb.add_structure(struct_name, struct_dump)


    @asyncio.coroutine
    def _handle_add_function(self,msg_inst):
        """
        Handle an AddFunction message.
        """
        func_name = msg_inst.get_field('func_name')
        func_comment = msg_inst.get_field('func_comment')
        func_data = msg_inst.get_field('func_data')

        logger.debug('AddFunction: func_name={}'
                ' func_comment={}'
                ' func_data={} on connection {}'.\
                        format(func_name,func_comment,func_data,\
                        id(self._msg_endpoint)))

        # Add function to database:
        self._fdb.add_function(func_name,func_data,func_comment)

    @asyncio.coroutine
    def _handle_request_func_names(self, msg_inst):
        func_names = self._fdb.get_func_names()
        resp_msg = cser_serializer.get_msg('ResponseFuncNames')
        logger.debug("Got all func names: {}".format(func_names))
        resp_msg.set_field('func_names', func_names)

        yield from self._msg_endpoint.send(resp_msg)

    @asyncio.coroutine
    def _handle_request_struct_names(self, msg_inst):
        struct_names = self._fdb.get_struct_names()
        resp_msg = cser_serializer.get_msg('ResponseStructNames')
        logger.debug("Got all struct names: {}".format(struct_names))
        resp_msg.set_field('struct_names', struct_names)

        yield from self._msg_endpoint.send(resp_msg)

    @asyncio.coroutine
    def _handle_request_struct(self, msg_inst):
        struct_name = msg_inst.get_field('struct_name')
        struct_dump = self._fdb.get_struct(struct_name)

        if struct_dump != None:
            resp_msg = cser_serializer.get_msg('ResponseStruct')
            resp_msg.set_field('struct_dump', struct_dump)
            yield from self._msg_endpoint.send(resp_msg)
        else:
            logger.debug('Try to get {} struct, got {} dump'\
                        .format(struct_name, struct_dump))

        
    @asyncio.coroutine
    def _handle_request_similars(self,msg_inst):
        """
        Handle a RequestSimilars message.
        """
        func_data = msg_inst.get_field('func_data')
        num_similars = msg_inst.get_field('num_similars')

        logger.debug('GetSimilars: func_data={}'
                ' num_similars={} on connection {}'.\
                        format(func_data,num_similars,\
                        id(self._msg_endpoint)))

        # Get a list of similar functions from the db:
        sims = self._fdb.get_similars(func_data,num_similars)

        # We convert the sims we have received from the db to another format:
        res_sims = []
        for s in sims:
            fs = FSimilar(name=s.func_name,\
                    comment=s.func_comment,\
                    sim_grade=s.func_grade)
            res_sims.append(fs)
        
        # Build a ResponseSimilars message:
        resp_msg = cser_serializer.get_msg('ResponseSimilars')
        resp_msg.set_field('similars',res_sims)

        # Send back the Response similars message:
        yield from self._msg_endpoint.send(resp_msg)

