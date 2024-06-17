import statistics
import argparse
import time
from datetime import datetime
from socket import *

# 消息格式：
# 序号 2字节，确认号 2字节，ver 1字节，信号1字节 SYN ACK FIN

# 创建IPv4与UDP套接字
UDPClientSocket = socket(AF_INET, SOCK_DGRAM)
UDPClientSocket.settimeout(0.1)  # 超时时间100ms

# 定义量
noMean = b"00-00-00"
seqNo = b"00"  # 客户端序号，之后对齐从01开始
cliVer = b"2"  # 客户端版本号
ack = b"00"  # 确认号
sendPacketNum = 12  # 包总数
receivedResponseNum = 0  # 收到回复数
RTTList = []  # 存储RTT的列表
firstResponseTime = None  # 第一次收到的时间
lastResponseTime = None  # 最后一次收到的时间
arqCount = 0  # 重传次数
i = sendPacketNum  # 循环次数

# 定义命令行，接收服务器IP与端口号
parser = argparse.ArgumentParser(description='UDP Client')
parser.add_argument('server_ip', type=str, help='IP address of the server')
parser.add_argument('server_port', type=int, help='Port number of the server')
args = parser.parse_args()
serverIP = args.server_ip
serverPort = args.server_port

# 模拟TCP握手链接
message = seqNo + b"00" + cliVer + b"4" + noMean  # 100
UDPClientSocket.sendto(message, (serverIP, serverPort))  # 发送第一次握手
print("First handshake successful")

response, _ = UDPClientSocket.recvfrom(1500)  # 接收第二次握手
signal = int.from_bytes(response[5:6], byteorder='big')
SYN = (signal >> 2) & 1
if SYN == 1:
    ack = response[0:2]  # 服务器开始地址
    # 序号加1，从01开始
    nextCliNo = int.from_bytes(seqNo, byteorder='big')
    nextCliNo += 1
    seqNo = nextCliNo.to_bytes((nextCliNo.bit_length() + 7) // 8, byteorder='big')

    # 确认号加1
    nextAck = int.from_bytes(ack, byteorder='big')
    nextAck += 1
    ack = nextAck.to_bytes((nextAck.bit_length() + 7) // 8, byteorder='big')

    message = seqNo + ack + cliVer + b"2" + noMean  # 010
    UDPClientSocket.sendto(message, (serverIP, serverPort))  # 发送第三次握手
    print("Third handshake successful")
    print("Start packets transmission\n")
else:
    print("Received second handshake failed")

# 开始传包
while i:
    # 生成包
    message = seqNo + ack + cliVer + b"0" + noMean  # 000

    try:
        startTime = time.time()
        UDPClientSocket.sendto(message, (serverIP, serverPort))  # 发送

        response, _ = UDPClientSocket.recvfrom(1500)  # 接收，必定接收成功的
        endTime = time.time()
        RTT = (endTime - startTime) * 1000  # 计算RTT，毫秒
        RTTList.append(RTT)

        # 获取数据
        signal = int.from_bytes(response[5:6], byteorder='big')
        ACK = (signal >> 1) & 1

        if ACK == 1:
            serTime = response[6:]  # 获取时间
            receivedResponseNum += 1
            print(
                f"seqNo: {int.from_bytes(seqNo, byteorder='big') - 12336},serverIP: {serverIP},"
                f"serverPort: {serverPort},RTT: {RTT:.2f}ms,serverTime: {serTime.decode('utf-8')}\n")
            if firstResponseTime is None:
                firstResponseTime = datetime.strptime(serTime.decode('utf-8'), "%H-%M-%S")
            lastResponseTime = datetime.strptime(serTime.decode('utf-8'), "%H-%M-%S")

            arqCount = 0
            # 序号加1
            nextCliNo = int.from_bytes(seqNo, byteorder='big')
            nextCliNo += 1
            seqNo = nextCliNo.to_bytes((nextCliNo.bit_length() + 7) // 8, byteorder='big')

            # 确认号加1
            nextAck = int.from_bytes(ack, byteorder='big')
            nextAck += 1
            ack = nextAck.to_bytes((nextAck.bit_length() + 7) // 8, byteorder='big')

            i -= 1
        else:
            print("Error, received a reply with an ACK value of 0")
    except timeout:
        # 两次重传
        arqCount += 1
        print(f"seqNo:{int.from_bytes(seqNo, byteorder='big') - 12336} request time out")

        if arqCount == 1:
            print("first retransmission")

        if arqCount == 2:
            print("second retransmission")

        if arqCount == 3:
            # 跳过该包
            print("skip the package\n")
            arqCount = 0
            # 序号加1
            nextCliNo = int.from_bytes(seqNo, byteorder='big')
            nextCliNo += 1
            seqNo = nextCliNo.to_bytes((nextCliNo.bit_length() + 7) // 8, byteorder='big')

            i -= 1

# 结束后统计信息
if receivedResponseNum > 0:
    maxRTT = max(RTTList)
    minRTT = min(RTTList)
    avgRTT = sum(RTTList) / len(RTTList)
    stddevRTT = statistics.stdev(RTTList)
    totalResponseTime = (
            lastResponseTime - firstResponseTime).total_seconds() if firstResponseTime and lastResponseTime else 0

    print("Summary:")
    print(f"received UDP response: {receivedResponseNum}")
    print(f"packet loss rate: {(1 - receivedResponseNum / sendPacketNum) * 100:.2f}%")
    print(f"max RTT: {maxRTT:.2f}ms")
    print(f"min RTT: {minRTT:.2f}ms")
    print(f"average RTT: {avgRTT:.2f}ms")
    print(f"RTT standard deviation: {stddevRTT:.2f}ms")
    print(f"total time: {totalResponseTime}s")
else:
    print("No response received")

# 模拟TCP关闭
# 确认号加1
nextAck = int.from_bytes(ack, byteorder='big')
nextAck += 1
ack = nextAck.to_bytes((nextAck.bit_length() + 7) // 8, byteorder='big')

message = seqNo + ack + cliVer + b"1" + noMean  # 001
UDPClientSocket.sendto(message, (serverIP, serverPort))  # 发送第一次挥手
print("Send the first wave")

response, _ = UDPClientSocket.recvfrom(1500)  # 接收第二次挥手

response, _ = UDPClientSocket.recvfrom(1500)  # 接收第三次挥手
# 序号加1
nextCliNo = int.from_bytes(seqNo, byteorder='big')
nextCliNo += 1
seqNo = nextCliNo.to_bytes((nextCliNo.bit_length() + 7) // 8, byteorder='big')
# 确认号加1
ack = response[0:2]
nextAck = int.from_bytes(ack, byteorder='big')
nextAck += 1
ack = nextAck.to_bytes((nextAck.bit_length() + 7) // 8, byteorder='big')

message = seqNo + ack + cliVer + b"2" + noMean  # 010
UDPClientSocket.sendto(message, (serverIP, serverPort))  # 发送第四次挥手
print("Send fourth wave")

# 关闭
time.sleep(0.5)  # 停0.5s，模拟客户端等待关闭的过程
UDPClientSocket.close()
