import pytest
import time
import sys
import os

# Add scripts directory to path to import breakers
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts')))

from breakers import CircuitBreaker

def test_circuit_opens_after_threshold_failures():
    cb = CircuitBreaker(failure_threshold=3, recovery_seconds=10)
    
    def failing_func():
        raise ValueError("Simulated failure")
        
    for _ in range(3):
        with pytest.raises(ValueError):
            cb.call(failing_func)
            
    # The 4th call should raise RuntimeError because the circuit is open
    with pytest.raises(RuntimeError) as exc_info:
        cb.call(failing_func)
    assert "Circuit open" in str(exc_info.value)

def test_circuit_blocks_calls_when_open(mocker):
    cb = CircuitBreaker(failure_threshold=1, recovery_seconds=10)
    mock_func = mocker.Mock(side_effect=ValueError("Simulated failure"))
    
    with pytest.raises(ValueError):
        cb.call(mock_func)
        
    mock_func.reset_mock()
    mock_func.side_effect = None # Make it successful
    
    with pytest.raises(RuntimeError):
        cb.call(mock_func)
        
    mock_func.assert_not_called()

def test_circuit_half_opens_after_recovery_seconds(mocker):
    cb = CircuitBreaker(failure_threshold=1, recovery_seconds=0) # 0 seconds to recover instantly
    
    def failing_func():
        raise ValueError("Simulated failure")
        
    with pytest.raises(ValueError):
        cb.call(failing_func)
        
    time.sleep(0.1) # Wait just a bit to ensure time.time() advances
    
    # Next call should go through and succeed
    mock_func = mocker.Mock(return_value="Success")
    result = cb.call(mock_func)
    
    assert result == "Success"
    assert cb.fail_count == 0
    assert cb.opened_at is None
