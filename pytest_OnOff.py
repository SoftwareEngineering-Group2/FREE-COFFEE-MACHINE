import unittest
from unittest.mock import patch, MagicMock

import Smart House Simulator as simulator  # simulator python file named: Smart House Simulator.py

class TestSimulatorFunctionality(unittest.TestCase):

    def setUp(self):
        # Reset simulator state before each test
        simulator.curtain_status = 'closed' 
        simulator.status = 'off'  # Coffee machine
        simulator.media_player_status = 'stop'

    @patch('SmartSimulator.sio')  
    def test_curtain_opens_correctly(self, mock_sio):
        test_data = [{'deviceName': 'curtain', 'deviceState': True}]
        mock_sio.emit.call_args = (('device-state-changed', test_data),)  

        simulator.on_device_state_changed(test_data)

        self.assertEqual(simulator.curtain_status, 'opened')  

    @patch('SmartSimulator.sio') 
    def test_curtain_closes_correctly(self, mock_sio):
        test_data = [{'deviceName': 'curtain', 'deviceState': False}]
        mock_sio.emit.call_args = (('device-state-changed', test_data),)  

        simulator.on_device_state_changed(test_data)

        self.assertEqual(simulator.curtain_status, 'closed')

    @patch('SmartSimulator.sio')  
    def test_curtain_invalid_state(self, mock_sio):
        test_data = [{'deviceName': 'curtain', 'deviceState': None}]  
        mock_sio.emit.call_args = (('device-state-changed', test_data),)  

        simulator.on_device_state_changed(test_data)

        self.assertEqual(simulator.curtain_status, 'closed')  # Assuming it ignores invalid states

    @patch('SmartSimulator.sio') 
    def test_coffee_machine_turns_on(self, mock_sio):
        test_data = [{'deviceName': 'coffeemachine', 'deviceState': True}]
        mock_sio.emit.call_args = (('device-state-changed', test_data),)  

        simulator.on_device_state_changed(test_data)

        self.assertEqual(simulator.status, 'on')  

    @patch('SmartSimulator.sio') 
    def test_coffee_machine_turns_off(self, mock_sio):
        test_data = [{'deviceName': 'coffeemachine', 'deviceState': False}]
        mock_sio.emit.call_args = (('device-state-changed', test_data),)  

        simulator.on_device_state_changed(test_data)

        self.assertEqual(simulator.status, 'off')

    @patch('SmartSimulator.sio') 
    def test_media_player_plays(self, mock_sio):
        test_data = [{'deviceName': 'mediaplayer', 'deviceState': True}]
        mock_sio.emit.call_args = (('device-state-changed', test_data),)  

        simulator.on_device_state_changed(test_data)

        self.assertEqual(simulator.media_player_status, 'play')

    @patch('SmartSimulator.sio') 
    def test_media_player_stops(self, mock_sio):
        test_data = [{'deviceName': 'mediaplayer', 'deviceState': False}]
        mock_sio.emit.call_args = (('device-state-changed', test_data),)  

        simulator.on_device_state_changed(test_data)

        self.assertEqual(simulator.media_player_status, 'stop') 

if __name__ == '__main__':
    unittest.main()
