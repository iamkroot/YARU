-- Store in lua plugins folder (Help > About Wireshark > Folders)

yaru_protocol = Proto("YARU", "YARU Protocol")

seq_num = ProtoField.uint64("yaru.seq_num", "seqnum", base.DEC)
message_length = ProtoField.uint16("yaru.message_length", "length", base.DEC)
checksum = ProtoField.bytes("yaru.checksum", "checksum")
isAck = ProtoField.bool("yaru.isAck", "isAck")
yaru_protocol.fields = {seq_num, message_length, checksum, isAck, data}

function yaru_protocol.dissector(buffer, pinfo, tree)
  length = buffer:len()
  if length == 0 then return end

  pinfo.cols.protocol = yaru_protocol.name

  local subtree = tree:add(yaru_protocol, buffer(), "YARU Protocol Data")
  subtree:add(seq_num, buffer(0,8))
  if buffer(8,2):int() == 0 then 
    subtree:add(isAck, 1)
  else
    subtree:add(message_length, buffer(8,2))
  end
  subtree:add(checksum, buffer(10,16))
end

local udp_port = DissectorTable.get("udp.port")
udp_port:add(1060, yaru_protocol)