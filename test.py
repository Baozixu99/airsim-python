import json
import socket
import numpy as np
require = socket.socket()
require.connect(("127.0.0.1", 65432))
state = np.array([0, 1, 1, 1, 1, 1])


json_str = json.dumps(state)  # 结果: '[1,0,1,1,0,1]'
        # 步骤2: 编码为字节
byte_data = json_str.encode('utf-8')  # 结果: b'[1,0,1,1,0,1]'
        # 步骤3: 发送完整数据
require.sendall(byte_data)
data = require.recv(1024)
response = json.loads(data.decode())