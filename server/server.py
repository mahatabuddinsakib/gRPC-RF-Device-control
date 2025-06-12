#!/usr/bin/env python3
"""
RF Control gRPC Server
Implements RF device control via gRPC with VISA/UHD API integration or simulation
"""

import grpc
from concurrent import futures
import time
import logging
import random
import json
from typing import Dict, Optional

# Import generated protobuf classes
import rfcontrol_pb2
import rfcontrol_pb2_grpc

# VISA/UHD simulation - replace with actual implementation
class RFDeviceSimulator:
    """Simulates an RF device with VISA/UHD-like interface"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.connected = False
        self.frequency = 2.4e9  # 2.4 GHz default
        self.gain = 0.0         # 0 dB default
        self.bandwidth = 20e6   # 20 MHz default
        self.antenna = "RX2"    # Default antenna
        self.temperature = 25.0 # Celsius
        
        # Device specifications (simulate USRP B200 series)
        self.specs = {
            "manufacturer": "Ettus Research",
            "model": "USRP B200",
            "serial_number": f"SN{random.randint(100000, 999999)}",
            "firmware_version": "4.1.0",
            "min_frequency": 70e6,    # 70 MHz
            "max_frequency": 6e9,     # 6 GHz
            "min_gain": -20.0,        # -20 dB
            "max_gain": 76.0          # 76 dB
        }
        
        self.connect()
    
    def connect(self) -> bool:
        """Simulate device connection"""
        try:
            # Simulate VISA/UHD connection
            logging.info(f"Connecting to RF device {self.device_id}")
            time.sleep(0.1)  # Simulate connection delay
            
            # Simulate occasional connection failures
            if random.random() < 0.05:  # 5% failure rate
                raise Exception("Device connection timeout")
            
            self.connected = True
            logging.info(f"Successfully connected to {self.device_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to connect to {self.device_id}: {e}")
            self.connected = False
            return False
    
    def set_frequency(self, freq: float) -> bool:
        """Set RF frequency (simulates UHD usrp.set_center_freq or VISA command)"""
        if not self.connected:
            return False
            
        if not (self.specs["min_frequency"] <= freq <= self.specs["max_frequency"]):
            logging.error(f"Frequency {freq/1e9:.3f} GHz out of range")
            return False
        
        # Simulate VISA command: "FREQ:CW {freq}"
        # Or UHD command: usrp.set_center_freq(freq)
        logging.info(f"Setting frequency to {freq/1e9:.3f} GHz")
        self.frequency = freq
        
        # Simulate slight temperature change due to frequency change
        self.temperature += random.uniform(-0.5, 0.5)
        return True
    
    def set_gain(self, gain: float) -> bool:
        """Set RF gain (simulates UHD usrp.set_gain or VISA command)"""
        if not self.connected:
            return False
            
        if not (self.specs["min_gain"] <= gain <= self.specs["max_gain"]):
            logging.error(f"Gain {gain} dB out of range")
            return False
        
        # Simulate VISA command: "POW:AMPL {gain}"
        # Or UHD command: usrp.set_gain(gain)
        logging.info(f"Setting gain to {gain} dB")
        self.gain = gain
        return True
    
    def set_bandwidth(self, bandwidth: float) -> bool:
        """Set RF bandwidth"""
        if not self.connected:
            return False
        
        # Simulate UHD command: usrp.set_rate(bandwidth)
        logging.info(f"Setting bandwidth to {bandwidth/1e6:.1f} MHz")
        self.bandwidth = bandwidth
        return True
    
    def set_antenna(self, antenna: str) -> bool:
        """Set antenna selection"""
        if not self.connected:
            return False
        
        valid_antennas = ["TX/RX", "RX2"]
        if antenna not in valid_antennas:
            logging.error(f"Invalid antenna {antenna}")
            return False
        
        # Simulate UHD command: usrp.set_antenna(antenna)
        logging.info(f"Setting antenna to {antenna}")
        self.antenna = antenna
        return True
    
    def get_idn(self) -> str:
        """Get device identification (simulates VISA *IDN? command)"""
        if not self.connected:
            return "DISCONNECTED"
        
        return f"{self.specs['manufacturer']},{self.specs['model']},{self.specs['serial_number']},{self.specs['firmware_version']}"
    
    def get_status(self) -> Dict:
        """Get current device status"""
        return {
            "device_id": self.device_id,
            "connected": self.connected,
            "frequency": self.frequency,
            "gain": self.gain,
            "bandwidth": self.bandwidth,
            "antenna": self.antenna,
            "temperature": self.temperature
        }


class RFControlServicer(rfcontrol_pb2_grpc.RFControlServiceServicer):
    """gRPC service implementation for RF device control"""
    
    def __init__(self):
        self.devices: Dict[str, RFDeviceSimulator] = {}
        self.logger = logging.getLogger(__name__)
    
    def _get_device(self, device_id: str) -> Optional[RFDeviceSimulator]:
        """Get or create RF device instance"""
        if device_id not in self.devices:
            self.logger.info(f"Creating new device instance: {device_id}")
            self.devices[device_id] = RFDeviceSimulator(device_id)
        
        return self.devices[device_id]
    
    def SetRFSettings(self, request, context):
        """Set RF configuration parameters"""
        self.logger.info(f"SetRFSettings called for device {request.device_id}")
        
        try:
            device = self._get_device(request.device_id)
            if not device:
                return rfcontrol_pb2.RFResponse(
                    success=False,
                    message="Failed to connect to device",
                    timestamp=int(time.time())
                )
            
            success = True
            messages = []
            
            # Set frequency if provided
            if request.frequency > 0:
                if device.set_frequency(request.frequency):
                    messages.append(f"Frequency set to {request.frequency/1e9:.3f} GHz")
                else:
                    success = False
                    messages.append("Failed to set frequency")
            
            # Set gain if provided
            if request.gain != 0:  # Allow negative gains
                if device.set_gain(request.gain):
                    messages.append(f"Gain set to {request.gain} dB")
                else:
                    success = False
                    messages.append("Failed to set gain")
            
            # Set bandwidth if provided
            if request.bandwidth > 0:
                if device.set_bandwidth(request.bandwidth):
                    messages.append(f"Bandwidth set to {request.bandwidth/1e6:.1f} MHz")
                else:
                    success = False
                    messages.append("Failed to set bandwidth")
            
            # Set antenna if provided
            if request.antenna:
                if device.set_antenna(request.antenna):
                    messages.append(f"Antenna set to {request.antenna}")
                else:
                    success = False
                    messages.append("Failed to set antenna")
            
            # Get current status
            status = device.get_status()
            device_status = rfcontrol_pb2.DeviceStatus(
                device_id=status["device_id"],
                connected=status["connected"],
                current_frequency=status["frequency"],
                current_gain=status["gain"],
                current_bandwidth=status["bandwidth"],
                current_antenna=status["antenna"],
                temperature=status["temperature"],
                status_message="Device operational" if success else "Configuration error"
            )
            
            return rfcontrol_pb2.RFResponse(
                success=success,
                message="; ".join(messages) if messages else "No changes requested",
                status=device_status,
                timestamp=int(time.time())
            )
            
        except Exception as e:
            self.logger.error(f"Error in SetRFSettings: {e}")
            return rfcontrol_pb2.RFResponse(
                success=False,
                message=f"Internal error: {str(e)}",
                timestamp=int(time.time())
            )
    
    def GetDeviceStatus(self, request, context):
        """Get current device status"""
        self.logger.info(f"GetDeviceStatus called for device {request.device_id}")
        
        try:
            device = self._get_device(request.device_id)
            status = device.get_status()
            
            return rfcontrol_pb2.DeviceStatus(
                device_id=status["device_id"],
                connected=status["connected"],
                current_frequency=status["frequency"],
                current_gain=status["gain"],
                current_bandwidth=status["bandwidth"],
                current_antenna=status["antenna"],
                temperature=status["temperature"],
                status_message="Device operational" if status["connected"] else "Device disconnected"
            )
            
        except Exception as e:
            self.logger.error(f"Error in GetDeviceStatus: {e}")
            return rfcontrol_pb2.DeviceStatus(
                device_id=request.device_id,
                connected=False,
                status_message=f"Error: {str(e)}"
            )
    
    def GetDeviceInfo(self, request, context):
        """Get device information"""
        self.logger.info(f"GetDeviceInfo called for device {request.device_id}")
        
        try:
            device = self._get_device(request.device_id)
            specs = device.specs
            
            return rfcontrol_pb2.DeviceInfo(
                device_id=request.device_id,
                manufacturer=specs["manufacturer"],
                model=specs["model"],
                serial_number=specs["serial_number"],
                firmware_version=specs["firmware_version"],
                min_frequency=specs["min_frequency"],
                max_frequency=specs["max_frequency"],
                min_gain=specs["min_gain"],
                max_gain=specs["max_gain"]
            )
            
        except Exception as e:
            self.logger.error(f"Error in GetDeviceInfo: {e}")
            return rfcontrol_pb2.DeviceInfo(
                device_id=request.device_id,
                manufacturer="Unknown",
                model="Error",
                serial_number="N/A",
                firmware_version="N/A"
            )


def serve():
    """Start the gRPC server"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    # Create gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rfcontrol_pb2_grpc.add_RFControlServiceServicer_to_server(
        RFControlServicer(), server
    )
    
    # Listen on port 50051
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting RF Control Server on {listen_addr}")
    server.start()
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.stop(0)


if __name__ == '__main__':
    serve()