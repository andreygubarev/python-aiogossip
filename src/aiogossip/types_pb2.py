# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: types.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0btypes.proto\"#\n\x07\x41\x64\x64ress\x12\n\n\x02ip\x18\x01 \x01(\x0c\x12\x0c\n\x04port\x18\x02 \x01(\x05\"5\n\x08\x45ndpoint\x12\x16\n\x04\x61\x64\x64r\x18\x01 \x01(\x0b\x32\x08.Address\x12\x11\n\treachable\x18\x02 \x01(\x08\"5\n\x04Node\x12\x0f\n\x07node_id\x18\x01 \x01(\x0c\x12\x1c\n\tendpoints\x18\x02 \x03(\x0b\x32\t.Endpoint\"I\n\x05Route\x12\x0f\n\x07node_id\x18\x01 \x01(\x0c\x12\x11\n\ttimestamp\x18\x02 \x01(\x03\x12\r\n\x05saddr\x18\x03 \x01(\t\x12\r\n\x05\x64\x61\x64\x64r\x18\x04 \x01(\t\"\x8f\x02\n\x07Message\x12\n\n\x02id\x18\x01 \x01(\x0c\x12\x1b\n\x04kind\x18\x02 \x03(\x0e\x32\r.Message.Kind\x12!\n\x07routing\x18\x03 \x01(\x0b\x32\x10.Message.Routing\x12\r\n\x05topic\x18\x04 \x01(\t\x12\x0f\n\x07payload\x18\x05 \x01(\x0c\x1a?\n\x07Routing\x12\r\n\x05snode\x18\x01 \x01(\x0c\x12\r\n\x05\x64node\x18\x02 \x01(\x0c\x12\x16\n\x06routes\x18\x03 \x03(\x0b\x32\x06.Route\"W\n\x04Kind\x12\r\n\tHANDSHAKE\x10\x00\x12\n\n\x06GOSSIP\x10\x01\x12\x07\n\x03SYN\x10\x02\x12\x07\n\x03\x41\x43K\x10\x03\x12\x07\n\x03PUB\x10\x04\x12\x07\n\x03SUB\x10\x05\x12\x07\n\x03REQ\x10\x06\x12\x07\n\x03RES\x10\x07\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'types_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_ADDRESS']._serialized_start=15
  _globals['_ADDRESS']._serialized_end=50
  _globals['_ENDPOINT']._serialized_start=52
  _globals['_ENDPOINT']._serialized_end=105
  _globals['_NODE']._serialized_start=107
  _globals['_NODE']._serialized_end=160
  _globals['_ROUTE']._serialized_start=162
  _globals['_ROUTE']._serialized_end=235
  _globals['_MESSAGE']._serialized_start=238
  _globals['_MESSAGE']._serialized_end=509
  _globals['_MESSAGE_ROUTING']._serialized_start=357
  _globals['_MESSAGE_ROUTING']._serialized_end=420
  _globals['_MESSAGE_KIND']._serialized_start=422
  _globals['_MESSAGE_KIND']._serialized_end=509
# @@protoc_insertion_point(module_scope)
