# gRPC-RF-Device-control

A gRPC-based client-server system for controlling RF devices with VISA/UHD API integration or mock logs simulation.

##  Architecture

```
┌─────────────┐    gRPC     ┌─────────────┐    VISA/UHD    ┌─────────────┐
│             │   (50051)   │             │      API       │             │
│   Client    │◄───────────►│   Server    │◄──────────────►│ RF Device   │
│             │             │             │                │             │
└─────────────┘             └─────────────┘                └─────────────┘
```


##  Installation

### Prerequisites

- Python 3.8+ 
- pip (Python package manager)
- Docker (optional, for containerized deployment)

### Step-by-Step Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate Protobuf Files**
   ```bash
   python -m grpc_tools.protoc \
       --proto_path=proto \
       --python_out=. \
       --grpc_python_out=. \
       proto/rfcontrol.proto
   ```

##  Project Structure (After Installation)

```
rf-control-system/
├── proto/
│   └── rfcontrol.proto         # gRPC service definition
├── server/
│   └── server.py              # gRPC server implementation
├── client/
│   └── client.py              # gRPC client with CLI
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container configuration
├── docker-compose.yml
├── rfcontrol_pb2              # protobuffer files
├── rfcontrol_pb2_grpc         # protobuffer files


```
##  Usage Examples

### Starting the Server

```bash
python server.py
```

Output:
```
2024-06-10 17:32:35,123 - __main__ - INFO - Starting RF Control Server on [::]:50051
```

### Client Commands

#### Interactive Mode
```bash
python client.py interactive
```

#### Command Line Interface
```bash
# Set RF parameters
python client.py set usrp0 -f 2.4e9 -g 20 -b 20e6 -a TX/RX

# Get device status
python client.py status usrp0

# Get device information
python client.py info usrp0
```

#### Interactive Session Example
```
rf_control> set usrp0 -f 2.4e9 -g 20 -b 20e6 -a TX/RX
Setting RF parameters for device 'usrp0'...
  Frequency: 2.400 GHz
  Gain: 20.0 dB
  Bandwidth: 20.0 MHz
  Antenna: TX/RX

Server Response:
  Success: ✓
  Message: Frequency set to 2.400 GHz; Gain set to 20.0 dB; Bandwidth set to 20.0 MHz; Antenna set to TX/RX
  Timestamp: Mon Jun 10 17:35:42 2024

Device Status:
  Connected: ✓
  Frequency: 2.400 GHz
  Gain: 20.0 dB
  Bandwidth: 20.0 MHz
  Antenna: TX/RX
  Temperature: 24.7°C
  Status: Device operational
```

##  VISA/UHD Integration

### Current Implementation (Simulation)

The current implementation simulates RF device behavior. The `RFDeviceSimulator` class in `server.py` mimics:

- **VISA Commands**: `*IDN?`, `FREQ:CW`, `POW:AMPL`
- **UHD Functions**: `set_center_freq()`, `set_gain()`, `set_rate()`

### Real VISA Integration

To integrate with real VISA devices, replace the `RFDeviceSimulator` class  with:

```python
import pyvisa

class RealVISADevice:
    def __init__(self, visa_address):
        rm = pyvisa.ResourceManager()
        self.device = rm.open_resource(visa_address)
    
    def set_frequency(self, freq):
        self.device.write(f"FREQ:CW {freq}")
        return True
    
    def get_idn(self):
        return self.device.query("*IDN?")
```

### Real UHD Integration

For UHD devices replace the `RFDeviceSimulator` class  with::

```python
import uhd

class RealUHDDevice:
    def __init__(self, device_args=""):
        self.usrp = uhd.usrp.MultiUSRP(device_args)
    
    def set_frequency(self, freq):
        self.usrp.set_rx_freq(freq)
        return True
    
    def set_gain(self, gain):
        self.usrp.set_rx_gain(gain)
        return True
```

##  Docker Deployment

### Build and Run

```bash
# Build the image
docker build -t rf-control-server .

# Run the container
docker run -p 50051:50051 rf-control-server
```

### Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f rf-server

# Stop services
docker-compose down
```

##  Monitoring and Logging

### Server Logs

The server provides detailed logging:

```
2024-06-10 17:32:35 - __main__ - INFO - Starting RF Control Server
2024-06-10 17:32:40 - __main__ - INFO - Creating new device instance: usrp0
2024-06-10 17:32:40 - __main__ - INFO - SetRFSettings called for device usrp0
```

### Health Checks

Docker containers include health checks:

```bash
# Check container health
docker-compose ps

# Manual health check
docker exec rf-control-server python -c "
import grpc
ch = grpc.insecure_channel('localhost:50051')
grpc.channel_ready_future(ch).result(timeout=5)
print('Server is healthy')
"
```

##  Security Considerations

Replace insecure channels with TLS encryption:

```python
# Server
credentials = grpc.ssl_server_credentials(private_key_cert_chain_pairs)
server.add_secure_port('[::]:50051', credentials)

# Client  
credentials = grpc.ssl_channel_credentials()
channel = grpc.secure_channel('server:50051', credentials)
```

## Troubleshoot Potential Issues

The server listens on port `50051` by default. To change this, modify the `listen_addr` in `server.py`:

```python
listen_addr = '[::]:50052'  # Change to desired port
```
To connect to a different server address:

```bash
python client.py --server hostname:50051 interactive
```
1. **Port Already in Use**
   ```bash
   # Find process using port 50051
   lsof -i :50051
   
   # Kill the process
   kill -9 <PID>
   ```

## gRPC Services

#### SetRFSettings
```protobuf
rpc SetRFSettings(RFConfig) returns (RFResponse);
```

#### GetDeviceStatus
```protobuf
rpc GetDeviceStatus(DeviceRequest) returns (DeviceStatus);
```

#### GetDeviceInfo
```protobuf
rpc GetDeviceInfo(DeviceRequest) returns (DeviceInfo);
```

### Message Types

See `proto/rfcontrol.proto` for detailed message definitions.
