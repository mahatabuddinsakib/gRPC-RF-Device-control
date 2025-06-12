#!/usr/bin/env python3
"""
RF Control gRPC Client
Provides CLI interface to control RF devices via gRPC
"""

import grpc
import argparse
import sys
from typing import Optional
import time

# Import generated protobuf classes
import rfcontrol_pb2
import rfcontrol_pb2_grpc


class RFControlClient:
    """Client for RF Control gRPC service"""
    
    def __init__(self, server_address='localhost:50051'):
        self.server_address = server_address
        self.channel = None
        self.stub = None
    
    def connect(self) -> bool:
        """Connect to the gRPC server"""
        try:
            self.channel = grpc.insecure_channel(self.server_address)
            self.stub = rfcontrol_pb2_grpc.RFControlServiceStub(self.channel)
            
            # Test connection with a simple call
            grpc.channel_ready_future(self.channel).result(timeout=5)
            print(f"✓ Connected to RF Control Server at {self.server_address}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to connect to server: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the gRPC server"""
        if self.channel:
            self.channel.close()
            print("Disconnected from server")
    
    def set_rf_settings(self, device_id: str, frequency: Optional[float] = None,
                       gain: Optional[float] = None, bandwidth: Optional[float] = None,
                       antenna: Optional[str] = None) -> bool:
        """Set RF configuration parameters"""
        if not self.stub:
            print("✗ Not connected to server")
            return False
        
        try:
            # Create RF configuration request
            config = rfcontrol_pb2.RFConfig(
                device_id=device_id,
                frequency=frequency or 0,
                gain=gain if gain is not None else 0,
                bandwidth=bandwidth or 0,
                antenna=antenna or ""
            )
            
            print(f"Setting RF parameters for device '{device_id}'...")
            if frequency:
                print(f"  Frequency: {frequency/1e9:.3f} GHz")
            if gain is not None:
                print(f"  Gain: {gain} dB")
            if bandwidth:
                print(f"  Bandwidth: {bandwidth/1e6:.1f} MHz")
            if antenna:
                print(f"  Antenna: {antenna}")
            
            # Send request to server
            response = self.stub.SetRFSettings(config)
            
            # Display response
            print(f"\nServer Response:")
            print(f"  Success: {'OK' if response.success else 'ERROR'}")
            print(f"  Message: {response.message}")
            print(f"  Timestamp: {time.ctime(response.timestamp)}")
            
            if response.status:
                print(f"\nDevice Status:")
                print(f"  Connected: {'OK' if response.status.connected else 'ERROR'}")
                print(f"  Frequency: {response.status.current_frequency/1e9:.3f} GHz")
                print(f"  Gain: {response.status.current_gain} dB")
                print(f"  Bandwidth: {response.status.current_bandwidth/1e6:.1f} MHz")
                print(f"  Antenna: {response.status.current_antenna}")
                print(f"  Temperature: {response.status.temperature:.1f}°C")
                print(f"  Status: {response.status.status_message}")
            
            return response.success
            
        except Exception as e:
            print(f" Error setting RF parameters: {e}")
            return False
    
    def get_device_status(self, device_id: str) -> bool:
        """Get current device status"""
        if not self.stub:
            print("ERROR: Not connected to server")
            return False
        
        try:
            request = rfcontrol_pb2.DeviceRequest(device_id=device_id)
            status = self.stub.GetDeviceStatus(request)
            
            print(f"\nDevice Status for '{device_id}':")
            print(f"  Connected: {'OK' if status.connected else 'ERROR'}")
            print(f"  Frequency: {status.current_frequency/1e9:.3f} GHz")
            print(f"  Gain: {status.current_gain} dB")
            print(f"  Bandwidth: {status.current_bandwidth/1e6:.1f} MHz")
            print(f"  Antenna: {status.current_antenna}")
            print(f"  Temperature: {status.temperature:.1f}°C")
            print(f"  Status: {status.status_message}")
            
            return status.connected
            
        except Exception as e:
            print(f"✗ Error getting device status: {e}")
            return False
    
    def get_device_info(self, device_id: str) -> bool:
        """Get device information"""
        if not self.stub:
            print("✗ Not connected to server")
            return False
        
        try:
            request = rfcontrol_pb2.DeviceRequest(device_id=device_id)
            info = self.stub.GetDeviceInfo(request)
            
            print(f"\nDevice Information for '{device_id}':")
            print(f"  Manufacturer: {info.manufacturer}")
            print(f"  Model: {info.model}")
            print(f"  Serial Number: {info.serial_number}")
            print(f"  Firmware Version: {info.firmware_version}")
            print(f"  Frequency Range: {info.min_frequency/1e6:.0f} - {info.max_frequency/1e9:.1f} GHz")
            print(f"  Gain Range: {info.min_gain} - {info.max_gain} dB")
            
            return True
            
        except Exception as e:
            print(f"✗ Error getting device info: {e}")
            return False
    
    def interactive_mode(self):
        """Interactive CLI mode"""
        print("\n" + "="*60)
        print("RF Control Client - Interactive Mode")
        print("="*60)
        print("Commands:")
        print("  set <device_id> [options]  - Set RF parameters")
        print("  status <device_id>         - Get device status")
        print("  info <device_id>           - Get device information")
        print("  help                       - Show this help")
        print("  quit                       - Exit")
        print("-"*60)
        
        while True:
            try:
                cmd = input("\nrf_control> ").strip().split()
                if not cmd:
                    continue
                
                if cmd[0].lower() in ['quit', 'exit', 'q']:
                    break
                elif cmd[0].lower() == 'help':
                    self._show_help()
                elif cmd[0].lower() == 'set':
                    self._handle_set_command(cmd)
                elif cmd[0].lower() == 'status':
                    if len(cmd) < 2:
                        print("Usage: status <device_id>")
                    else:
                        self.get_device_status(cmd[1])
                elif cmd[0].lower() == 'info':
                    if len(cmd) < 2:
                        print("Usage: info <device_id>")
                    else:
                        self.get_device_info(cmd[1])
                else:
                    print(f"Unknown command: {cmd[0]}. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _show_help(self):
        """Show detailed help"""
        print("\nDetailed Command Help:")
        print("-"*40)
        print("set <device_id> [options]:")
        print("  -f, --frequency <Hz>    Set frequency (e.g., 2.4e9 for 2.4 GHz)")
        print("  -g, --gain <dB>         Set gain (e.g., 20)")
        print("  -b, --bandwidth <Hz>    Set bandwidth (e.g., 20e6 for 20 MHz)")
        print("  -a, --antenna <name>    Set antenna (TX/RX or RX2)")
        print("\nExamples:")
        print("  set usrp0 -f 2.4e9 -g 20 -b 20e6 -a TX/RX")
        print("  set device1 --frequency 915e6 --gain 10")
        print("  status usrp0")
        print("  info device1")
    
    def _handle_set_command(self, cmd):
        """Handle the 'set' command with argument parsing"""
        if len(cmd) < 2:
            print("Usage: set <device_id> [options]")
            return
        
        device_id = cmd[1]
        args = cmd[2:]
        
        frequency = None
        gain = None
        bandwidth = None
        antenna = None
        
        i = 0
        while i < len(args):
            arg = args[i]
            
            if arg in ['-f', '--frequency'] and i + 1 < len(args):
                try:
                    frequency = float(args[i + 1])
                    i += 2
                except ValueError:
                    print(f"Invalid frequency: {args[i + 1]}")
                    return
            elif arg in ['-g', '--gain'] and i + 1 < len(args):
                try:
                    gain = float(args[i + 1])
                    i += 2
                except ValueError:
                    print(f"Invalid gain: {args[i + 1]}")
                    return
            elif arg in ['-b', '--bandwidth'] and i + 1 < len(args):
                try:
                    bandwidth = float(args[i + 1])
                    i += 2
                except ValueError:
                    print(f"Invalid bandwidth: {args[i + 1]}")
                    return
            elif arg in ['-a', '--antenna'] and i + 1 < len(args):
                antenna = args[i + 1]
                i += 2
            else:
                print(f"Unknown option: {arg}")
                return
        
        self.set_rf_settings(device_id, frequency, gain, bandwidth, antenna)


def parse_frequency(freq_str: str) -> float:
    """Parse frequency string with units"""
    freq_str = freq_str.lower()
    if freq_str.endswith('ghz'):
        return float(freq_str[:-3]) * 1e9
    elif freq_str.endswith('mhz'):
        return float(freq_str[:-3]) * 1e6
    elif freq_str.endswith('khz'):
        return float(freq_str[:-3]) * 1e3
    else:
        return float(freq_str)


def parse_bandwidth(bw_str: str) -> float:
    """Parse bandwidth string with units"""
    bw_str = bw_str.lower()
    if bw_str.endswith('mhz'):
        return float(bw_str[:-3]) * 1e6
    elif bw_str.endswith('khz'):
        return float(bw_str[:-3]) * 1e3
    else:
        return float(bw_str)


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='RF Control gRPC Client')
    parser.add_argument('--server', default='localhost:50051',
                       help='Server address (default: localhost:50051)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Set command
    set_parser = subparsers.add_parser('set', help='Set RF parameters')
    set_parser.add_argument('device_id', help='Device ID')
    set_parser.add_argument('-f', '--frequency', type=str,
                           help='Frequency (supports units: GHz, MHz, KHz)')
    set_parser.add_argument('-g', '--gain', type=float, help='Gain in dB')
    set_parser.add_argument('-b', '--bandwidth', type=str,
                           help='Bandwidth (supports units: MHz, KHz)')
    set_parser.add_argument('-a', '--antenna', help='Antenna selection')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get device status')
    status_parser.add_argument('device_id', help='Device ID')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get device information')
    info_parser.add_argument('device_id', help='Device ID')
    
    # Interactive command
    subparsers.add_parser('interactive', help='Start interactive mode')
    
    args = parser.parse_args()
    
    # Create client and connect
    client = RFControlClient(args.server)
    if not client.connect():
        return 1
    
    try:
        if args.command == 'set':
            frequency = parse_frequency(args.frequency) if args.frequency else None
            bandwidth = parse_bandwidth(args.bandwidth) if args.bandwidth else None
            
            success = client.set_rf_settings(
                args.device_id, frequency, args.gain, bandwidth, args.antenna
            )
            return 0 if success else 1
            
        elif args.command == 'status':
            success = client.get_device_status(args.device_id)
            return 0 if success else 1
            
        elif args.command == 'info':
            success = client.get_device_info(args.device_id)
            return 0 if success else 1
            
        elif args.command == 'interactive':
            client.interactive_mode()
            return 0
            
        else:
            # No command specified, start interactive mode
            client.interactive_mode()
            return 0
            
    finally:
        client.disconnect()


if __name__ == '__main__':
    sys.exit(main())