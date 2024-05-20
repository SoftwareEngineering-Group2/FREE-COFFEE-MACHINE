import unittest
from unittest.mock import patch, Mock, call
from SmartHouseSimulator_newUI import (
    on_complete_device_information,
    on_device_state_changed,
    draw_devices,
    status,
    coffee_type,
    brewing,
    curtain_status,
    microoven_status,
    media_player_status,
    current_track,
    curtain_width,
    curtain_target_width,
    animation_speed,
    brew_start_time
)
import time

class TestSmartHomeSimulator(unittest.TestCase):

    @patch('SmartHouseSimulator_newUI.pygame.draw.rect')
    @patch('SmartHouseSimulator_newUI.pygame.draw.circle')
    @patch('SmartHouseSimulator_newUI.pygame.display.flip')
    @patch('SmartHouseSimulator_newUI.pygame.font.Font')
    @patch('SmartHouseSimulator_newUI.screen', new_callable=Mock)
    def test_draw_devices(self, mock_screen, mock_font, mock_flip, mock_draw_circle, mock_draw_rect):
        print("Running test_draw_devices")

        # Set up the state
        global status, coffee_type, brewing, curtain_status, microoven_status, media_player_status, current_track
        status = 'on'
        coffee_type = 'Espresso'
        brewing = True
        curtain_status = 'closed'
        microoven_status = 'on'
        media_player_status = 'play'
        current_track = 1
        curtain_width = 0
        curtain_target_width = 150
        animation_speed = 10
        brew_start_time = time.time()

        # Mock the fill method
        mock_screen.fill = Mock()
        # Mock the blit method
        mock_screen.blit = Mock()
        # Mock font rendering to return a simple surface
        mock_font_instance = Mock()
        mock_font_instance.render.return_value = Mock()
        mock_font.return_value = mock_font_instance

        # Run the draw_devices function
        draw_devices()

        # Check that the screen is filled with WHITE color
        mock_screen.fill.assert_called_once_with((255, 255, 255))

        # Check that rectangles (for the devices) are drawn
        self.assertTrue(mock_draw_rect.called, "Expected pygame.draw.rect to be called")

        # Check that circles (for the on/off buttons) are drawn
        self.assertTrue(mock_draw_circle.called, "Expected pygame.draw.circle to be called")

        # Check that text is rendered and blitted to the screen
        self.assertTrue(mock_screen.blit.called, "Expected screen.blit to be called to draw text on screen")

        print("Finished test_draw_devices")

    @patch('SmartHouseSimulator_newUI.draw_devices')
    @patch('SmartHouseSimulator_newUI.pygame.display.flip')
    def test_on_complete_device_information_on_off(self, mock_flip, mock_draw_devices):
        print("Running test_on_complete_device_information_on_off")
        data = [
            {
                'deviceName': 'coffeeMachine',
                'deviceState': True,
            },
            {
                'deviceName': 'curtain',
                'deviceState': False,
            },
            {
                'deviceName': 'microOven',
                'deviceState': True,
            }
        ]
        on_complete_device_information(data)
        mock_draw_devices.assert_called_once()
        mock_flip.assert_called_once()
        self.assertTrue(mock_draw_devices.called, "Expected draw_devices to be called once")
        self.assertTrue(mock_flip.called, "Expected pygame.display.flip to be called once")
        print("Finished test_on_complete_device_information_on_off")

    @patch('SmartHouseSimulator_newUI.draw_devices')
    @patch('SmartHouseSimulator_newUI.pygame.display.flip')
    def test_on_device_state_changed_on_off(self, mock_flip, mock_draw_devices):
        print("Running test_on_device_state_changed_on_off")
        data = [
            {
                'deviceName': 'curtain',
                'deviceState': True
            },
            {
                'deviceName': 'coffeeMachine',
                'deviceState': True,
            },
            {
                'deviceName': 'microOven',
                'deviceState': False,
            }
        ]
        on_device_state_changed(data)
        mock_draw_devices.assert_called_once()
        mock_flip.assert_called_once()
        self.assertTrue(mock_draw_devices.called, "Expected draw_devices to be called once")
        self.assertTrue(mock_flip.called, "Expected pygame.display.flip to be called once")
        print("Finished test_on_device_state_changed_on_off")

    @patch('SmartHouseSimulator_newUI.draw_devices')
    @patch('SmartHouseSimulator_newUI.pygame.display.flip')
    def test_state_persistence_on_complete_device_information(self, mock_flip, mock_draw_devices):
        print("Running test_state_persistence_on_complete_device_information")
        # Initial state
        initial_data = [
            {
                'deviceName': 'coffeeMachine',
                'deviceState': True,
            },
            {
                'deviceName': 'curtain',
                'deviceState': False,
            },
            {
                'deviceName': 'microOven',
                'deviceState': True,
            }
        ]
        on_complete_device_information(initial_data)
        mock_draw_devices.assert_called()
        mock_flip.assert_called()
        self.assertTrue(mock_draw_devices.called, "Expected draw_devices to be called for initial state")
        self.assertTrue(mock_flip.called, "Expected pygame.display.flip to be called for initial state")

        # New state
        new_data = [
            {
                'deviceName': 'coffeeMachine',
                'deviceState': False,
            },
            {
                'deviceName': 'curtain',
                'deviceState': True,
            },
            {
                'deviceName': 'microOven',
                'deviceState': False,
            }
        ]
        on_complete_device_information(new_data)
        mock_draw_devices.assert_called()
        mock_flip.assert_called()
        self.assertTrue(mock_draw_devices.called, "Expected draw_devices to be called for new state")
        self.assertTrue(mock_flip.called, "Expected pygame.display.flip to be called for new state")
        print("Finished test_state_persistence_on_complete_device_information")

    @patch('SmartHouseSimulator_newUI.draw_devices')
    @patch('SmartHouseSimulator_newUI.pygame.display.flip')
    def test_state_persistence_on_device_state_changed(self, mock_flip, mock_draw_devices):
        print("Running test_state_persistence_on_device_state_changed")
        # Initial state change
        initial_data = [
            {
                'deviceName': 'curtain',
                'deviceState': True
            },
            {
                'deviceName': 'coffeeMachine',
                'deviceState': True,
            },
            {
                'deviceName': 'microOven',
                'deviceState': False,
            }
        ]
        on_device_state_changed(initial_data)
        mock_draw_devices.assert_called()
        mock_flip.assert_called()
        self.assertTrue(mock_draw_devices.called, "Expected draw_devices to be called for initial state change")
        self.assertTrue(mock_flip.called, "Expected pygame.display.flip to be called for initial state change")

        # New state change
        new_data = [
            {
                'deviceName': 'curtain',
                'deviceState': False
            },
            {
                'deviceName': 'coffeeMachine',
                'deviceState': False,
            },
            {
                'deviceName': 'microOven',
                'deviceState': True,
            }
        ]
        on_device_state_changed(new_data)
        mock_draw_devices.assert_called()
        mock_flip.assert_called()
        self.assertTrue(mock_draw_devices.called, "Expected draw_devices to be called for new state change")
        self.assertTrue(mock_flip.called, "Expected pygame.display.flip to be called for new state change")
        print("Finished test_state_persistence_on_device_state_changed")

if __name__ == '__main__':
    unittest.main(verbosity=2)
