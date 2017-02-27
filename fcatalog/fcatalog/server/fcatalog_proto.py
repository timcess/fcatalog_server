import collections
import logging
from fcatalog.proto.serializer import s_string,d_string,\
        s_blob,d_blob,s_uint32,d_uint32,\
        Serializer,ProtoDef,MsgDef



logger = logging.getLogger(__name__)
# A similar function struct
FSimilar = collections.namedtuple('FSimilar',\
        ['name','comment','sim_grade'])

class ChooseDB(MsgDef):
    afields = ['db_name']
    def serialize(self,msg_inst) -> bytes:
        """
        Serialize a msg_inst into bytes.
        """
        return s_string(msg_inst.get_field('db_name'))

    def deserialize(self,msg_data:bytes):
        """
        Deserialize data bytes into a msg_inst.
        """
        msg_inst = self.get_msg()
        nextl,db_name = d_string(msg_data)
        msg_inst.set_field('db_name',db_name)
        return msg_inst

class AddStructure(MsgDef):
    afields = ['struct_name', 'struct_value']
    def serialize(self, msg_inst) -> bytes:
        pass

    def deserialize(self, msg_data:bytes):
        i = msg_data.find(b'\x00')
        struct_name = msg_data[:i].decode('ascii')
        struct_dump = msg_data[i+1:]
        msg_inst = self.get_msg()
        logger.debug("Struct Name: {}\nStruct Dump: '{}'".format(struct_name, struct_dump))
        msg_inst.set_field('struct_name', struct_name)
        msg_inst.set_field('struct_value', struct_dump)

        return msg_inst

class RequestStructNames(MsgDef):
    afields = ['']
    def serialize(self, msg_inst) -> bytes:
        pass

    def deserialize(self, msg_data:bytes):
        msg_inst = self.get_msg()
        return msg_inst

class ResponseStructNames(MsgDef):
    afields = ['struct_names']
    def serialize(self, msg_inst) -> bytes:

        struct_names = msg_inst.get_field('struct_names')
        ser = b'\x00'.join(map(lambda x: x.encode('ascii'),\
                               struct_names))
        return ser

    def deserialize(self, msg_data:bytes):
        pass

class RequestFuncNames(MsgDef):
    afields = ['']
    def serialize(self, msg_inst) -> bytes:
        pass

    def deserialize(self, msg_data:bytes):
        msg_inst = self.get_msg()
        return msg_inst

class ResponseFuncNames(MsgDef):
    afields = ['func_names']
    def serialize(self, msg_inst) -> bytes:

        struct_names = msg_inst.get_field('func_names')
        ser = b'\x00'.join(map(lambda x: x.encode('ascii'),\
                               struct_names))
        return ser

    def deserialize(self, msg_data:bytes):
        pass

class RequestStruct(MsgDef):
    afields = ['struct_name']
    def serialize(self, msg_inst) -> bytes:
        pass

    def deserialize(self, msg_data:bytes):
        msg_inst = self.get_msg()
        struct_name = msg_data.decode('ascii')
        msg_inst.set_field('struct_name', struct_name)
        return msg_inst

class ResponseStruct(MsgDef):
    afields = ['struct_dump']
    def serialize(self, msg_inst) -> bytes:
        struct_dump = msg_inst.get_field('struct_dump')
        logger.debug("Structure Response: {}".format(struct_dump))

        ser = struct_dump

        return ser

    def deserialize(self, msg_data:bytes):
        pass

class SYN(MsgDef):
    def deserialize(self, msg_data:bytes):
        msg_inst = self.get_msg()
        return msg_inst

class ACK(MsgDef):
    def serialize(self, msg_inst) -> bytes:
        return ''


class AddFunction(MsgDef):
    afields = ['func_name','func_comment','func_data']
    def serialize(self,msg_inst) -> bytes:
        """
        Serialize a msg_inst into bytes.
        """
        resl = []
        resl.append(s_string(msg_inst.get_field('func_name')))
        resl.append(s_string(msg_inst.get_field('func_comment')))
        resl.append(s_blob(msg_inst.get_field('func_data')))
        return b''.join(resl)

    def deserialize(self,msg_data:bytes):
        """
        Deserialize data bytes into a msg_inst.
        """
        nl,func_name = d_string(msg_data)
        msg_data = msg_data[nl:]
        nl,func_comment = d_string(msg_data)
        msg_data = msg_data[nl:]
        nl,func_data = d_blob(msg_data)

        msg_inst = self.get_msg()
        msg_inst.set_field('func_name',func_name)
        msg_inst.set_field('func_comment',func_comment)
        msg_inst.set_field('func_data',func_data)
        return msg_inst


class RequestSimilars(MsgDef):
    afields = ['func_data','num_similars']
    def serialize(self,msg_inst) -> bytes:
        """
        Serialize a msg_inst into bytes.
        """
        resl = []
        resl.append(s_blob(msg_inst.get_field('func_data')))
        resl.append(s_uint32(msg_inst.get_field('num_similars')))
        return b''.join(resl)

    def deserialize(self,msg_data:bytes):
        """
        Deserialize data bytes into a msg_inst.
        """
        nl,func_data = d_blob(msg_data)
        msg_data = msg_data[nl:]
        nl,num_similars = d_uint32(msg_data)

        msg_inst = self.get_msg()
        msg_inst.set_field('func_data',func_data)
        msg_inst.set_field('num_similars',num_similars)
        return msg_inst


class ResponseSimilars(MsgDef):
    afields = ['similars']
    def serialize(self,msg_inst) -> bytes:
        """
        Serialize a msg_inst into bytes.
        """
        sims = msg_inst.get_field('similars')
        resl = []
        resl.append(s_uint32(len(sims)))
        
        for sim in sims:
            resl.append(s_string(sim.name))
            resl.append(s_string(sim.comment))
            resl.append(s_uint32(sim.sim_grade))

        return b''.join(resl)


    def deserialize(self,msg_data:bytes):
        """
        Deserialize data bytes into a msg_inst.
        """
        # Read the amount of similars:
        nl,num_sims = d_uint32(msg_data)
        msg_data = msg_data[nl:]

        sims = []
        for _ in range(num_sims):
            nl,sim_name = d_string(msg_data)
            msg_data = msg_data[nl:]
            nl,sim_comment = d_string(msg_data)
            msg_data = msg_data[nl:]
            nl,sim_grade = d_uint32(msg_data)
            msg_data = msg_data[nl:]

            sims.append(FSimilar(\
                    name=sim_name,\
                    comment=sim_comment,\
                    sim_grade=sim_grade\
                    ))

        msg_inst = self.get_msg()
        msg_inst.set_field('similars',sims)
        return msg_inst


class FCatalogProtoDef(ProtoDef):
    incoming_msgs = {\
        0:ChooseDB,\
        1:AddFunction,\
        2:RequestSimilars, \
        4:AddStructure, \
        5:RequestStructNames, \
        7:RequestStruct, \
        9:SYN,\
        11:RequestFuncNames}

    outgoing_msgs = {\
        3:ResponseSimilars,\
        6:ResponseStructNames,\
        8:ResponseStruct,\
        10:ACK,\
        12:ResponseFuncNames}




cser_serializer = Serializer(FCatalogProtoDef)

###############################################################
###############################################################

