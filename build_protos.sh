# Set the path for the OmniProtos directory
PROTO_DIR="OmniProtos" 
PROTO_FILES="$(find ${PROTO_DIR} -iname "*.proto")"

# Rebuilding twice in a row makes protoc complain.
# This exits before protoc and error.
if [ -f "device_pb2.py" ]; then
  exit 0
fi

# This calls the protoc protobuf compiler with the correct include
# directory and protobuf files. 
mkdir protos 
python -m grpc.tools.protoc -I${PROTO_DIR} --python_out=./protos --grpc_python_out=./protos ${PROTO_FILES}

# The protobuf compiler will create the proper folder structure
# but it won't create a proper python package. We need to add the
# __init__ file manually in order for python to recognize the
# folder as a proper package.
touch protos/__init__.py

