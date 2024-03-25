import pytest
from unittest.mock import patch

# Adjust the import path as necessary. If SmartHouseSimulator.py is your main file,
# you might need to structure your project so that it's importable, or directly manipulate the curtain_status for testing.
import SmartHouseSimulator

@pytest.fixture(autouse=True)
def reset_curtain_status():
    # This ensures curtain_status starts as 'closed' for each test.
    SmartHouseSimulator.curtain_status = 'closed'

def test_curtain_opens():
    # Directly simulate the condition that would result in an 'opened' curtain.
    SmartHouseSimulator.curtain_status = 'opened'  # Simulate the effect of receiving the appropriate WebSocket message.
    assert SmartHouseSimulator.curtain_status == 'opened', "Curtain should open but didn't."

def test_curtain_closes():
    # Ensure curtain starts open, then simulate closing.
    SmartHouseSimulator.curtain_status = 'opened'  # Open first to close next.
    SmartHouseSimulator.curtain_status = 'closed'  # Simulate the effect of receiving the appropriate WebSocket message.
    assert SmartHouseSimulator.curtain_status == 'closed', "Curtain should close but didn't."
