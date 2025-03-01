#!/usr/bin/env python3
"""
Redis client for testing Predixy proxy with a Redis cluster.
This client connects to the Predixy proxy and performs various Redis operations.
It also includes functions to test how Predixy handles server errors.
"""

import redis
import time
import random
import argparse
import sys


class RedisProxyClient:
    def __init__(self, host="localhost", port=7617, db=0):
        """Initialize Redis client connecting to Predixy proxy."""
        self.host = host
        self.port = port
        self.db = db
        self.client = self._connect()

    def _connect(self):
        """Connect to Redis via Predixy proxy."""
        try:
            client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
            # Test connection
            client.ping()
            print(f"Successfully connected to Predixy at {self.host}:{self.port}")
            return client
        except redis.ConnectionError as e:
            print(f"Failed to connect to Predixy: {e}")
            sys.exit(1)

    def set_key(self, key, value):
        """Set a key-value pair."""
        try:
            return self.client.set(key, value)
        except Exception as e:
            print(f"Error setting key {key}: {e}")
            return False

    def get_key(self, key):
        """Get a value by key."""
        try:
            return self.client.get(key)
        except Exception as e:
            print(f"Error getting key {key}: {e}")
            return None

    def delete_key(self, key):
        """Delete a key."""
        try:
            return self.client.delete(key)
        except Exception as e:
            print(f"Error deleting key {key}: {e}")
            return False

    def run_basic_operations(self, num_ops=100):
        """Run a series of basic Redis operations."""
        print(f"Running {num_ops} basic operations...")

        for i in range(num_ops):
            key = f"test:key:{i}"
            value = f"value-{i}"

            # Set key
            self.set_key(key, value)

            # Get key
            result = self.get_key(key)
            if result:
                print(f"Key {key} = {result.decode('utf-8')}")

            # Sleep briefly to avoid overwhelming the server
            time.sleep(0.01)

        print("Basic operations completed.")

    def test_error_handling(self):
        """Test how Predixy handles errors by sending malformed commands."""
        print("Testing error handling...")

        try:
            # Try to execute a non-existent command
            self.client.execute_command("NONEXISTENT_COMMAND")
        except redis.ResponseError as e:
            print(f"Expected error for non-existent command: {e}")

        try:
            # Try to execute HGET with wrong number of arguments
            self.client.execute_command("HGET")
        except redis.ResponseError as e:
            print(f"Expected error for wrong number of arguments: {e}")

        print("Error handling tests completed.")

    def simulate_high_load(self, duration=10, threads=5):
        """Simulate high load by sending many requests in parallel."""
        print(f"Simulating high load for {duration} seconds...")

        import threading

        def worker():
            end_time = time.time() + duration
            ops = 0

            while time.time() < end_time:
                key = f"load:key:{random.randint(1, 1000)}"
                value = f"load-value-{random.randint(1, 1000)}"

                self.set_key(key, value)
                self.get_key(key)

                ops += 2
                time.sleep(0.001)  # Small delay to prevent CPU overload

            print(f"Worker completed {ops} operations")

        # Start worker threads
        workers = []
        for i in range(threads):
            t = threading.Thread(target=worker)
            t.start()
            workers.append(t)

        # Wait for all workers to complete
        for t in workers:
            t.join()

        print("High load simulation completed.")


def main():
    parser = argparse.ArgumentParser(description="Redis Proxy Client")
    parser.add_argument("--host", default="localhost", help="Predixy host")
    parser.add_argument("--port", type=int, default=7617, help="Predixy port")
    parser.add_argument(
        "--ops", type=int, default=100, help="Number of operations to run"
    )
    parser.add_argument(
        "--test-errors", action="store_true", help="Test error handling"
    )
    parser.add_argument("--high-load", action="store_true", help="Simulate high load")
    parser.add_argument(
        "--load-duration",
        type=int,
        default=10,
        help="Duration of high load test in seconds",
    )
    parser.add_argument(
        "--threads", type=int, default=5, help="Number of threads for high load test"
    )

    args = parser.parse_args()

    client = RedisProxyClient(host=args.host, port=args.port)

    # Run basic operations
    client.run_basic_operations(num_ops=args.ops)

    # Test error handling if requested
    if args.test_errors:
        client.test_error_handling()

    # Simulate high load if requested
    if args.high_load:
        client.simulate_high_load(duration=args.load_duration, threads=args.threads)


if __name__ == "__main__":
    main()
