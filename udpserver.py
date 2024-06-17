import random
from datetime import datetime
from socket import *

# 定义量
noMean = b"00-00-00"
serverIP = "localhost"  # 服务器IP
serverPort = 10101  # 服务器端口号
lossRate = 0.5  # 丢包率
seqNo = b"00"  # 服务器序号，对齐后从1开始
serVer = b"2"  # 服务器版本号

# 创建IPv4与UDP套接字，并绑定
UDPServerSocket = socket(AF_INET, SOCK_DGRAM)
UDPServerSocket.bind((serverIP, serverPort))
print(f"UDP server is running on {serverIP}:{serverPort}")

message, UDPClientAdd = UDPServerSocket.recvfrom(1500)  # 接收第一次握手
signal = int.from_bytes(message[5:6], byteorder='big')
SYN = (signal >> 2) & 1
if SYN == 1:
    cliSeqNo = message[0:2]
    # 确认号加1
    ack = int.from_bytes(cliSeqNo, byteorder='big')
    ack += 1
    ack = ack.to_bytes((ack.bit_length() + 7) // 8, byteorder='big')

    response = seqNo + ack + serVer + b"6" + noMean  # 110
    UDPServerSocket.sendto(response, UDPClientAdd)  # 发送第二次握手
    print("Second handshake successful")

    message, UDPClientAdd = UDPServerSocket.recvfrom(1500)  # 接收第三次握手
    signal = int.from_bytes(message[5:6], byteorder='big')
    ACK = (signal >> 1) & 1
    if ACK == 1:
        # 序号加1，从01开始
        nextSeqNo = int.from_bytes(seqNo, byteorder='big')
        nextSeqNo += 1
        seqNo = nextSeqNo.to_bytes((nextSeqNo.bit_length() + 7) // 8, byteorder='big')
        print("Received ACK for the third handshake")
    else:
        print("The ACK signal for the third handshake is 0")
else:
    print("Received first handshake failure")

# 持续监听
while True:
    message, UDPClientAdd = UDPServerSocket.recvfrom(1500)  # 接收1500字节数据

    signal = int.from_bytes(message[5:6], byteorder='big')
    SYN = (signal >> 2) & 1
    ACK = (signal >> 1) & 1
    FIN = signal & 1

    # 挥手过程
    if FIN == 1:
        # 序列号加1
        nextSeqNo = int.from_bytes(seqNo, byteorder='big')
        nextSeqNo += 1
        seqNo = nextSeqNo.to_bytes((nextSeqNo.bit_length() + 7) // 8, byteorder='big')

        # 获取数据
        ack = message[0:2]  # 接收到客户端这个位置的数据了
        # 期望收到该位置数据
        nextAck = int.from_bytes(ack, byteorder='big')
        nextAck += 1
        ack = nextAck.to_bytes((nextAck.bit_length() + 7) // 8, byteorder='big')

        response = seqNo + ack + serVer + b"2" + noMean  # 010
        UDPServerSocket.sendto(response, UDPClientAdd)  # 发送第二次挥手
        print("Send the second wave")

        response = seqNo + ack + serVer + b"3" + noMean  # 011
        UDPServerSocket.sendto(response, UDPClientAdd)  # 发送第三次挥手
        print("Send the third wave")
        break

    # 由于基本能接收，这里模拟没接收的情况
    else:
        if random.random() > lossRate:
            # 构造回复报文
            # 序列号加1
            nextSeqNo = int.from_bytes(seqNo, byteorder='big')
            nextSeqNo += 1
            seqNo = nextSeqNo.to_bytes((nextSeqNo.bit_length() + 7) // 8, byteorder='big')

            # 获取数据
            ack = message[0:2]  # 接收到客户端这个位置的数据了
            # 期望收到该位置数据
            nextAck = int.from_bytes(ack, byteorder='big')
            nextAck += 1
            ack = nextAck.to_bytes((nextAck.bit_length() + 7) // 8, byteorder='big')

            serverTime = datetime.now().strftime("%H-%M-%S").encode("utf-8")  # 回复时间
            response = seqNo + ack + serVer + b"2" + serverTime  # 010
            UDPServerSocket.sendto(response, UDPClientAdd)  # 回复
            print(f"send response to client{UDPClientAdd}")
        else:
            print(f"loss the message from client{UDPClientAdd}")

# 关闭套接字
message, UDPClientAdd = UDPServerSocket.recvfrom(1500)  # 接收第四次挥手后关闭
UDPServerSocket.close()
