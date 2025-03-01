#!/usr/bin/env python3
"""
Test script to simulate Redis server failures and observe how Predixy handles them.
This script will:
1. Connect to the Predixy proxy
2. Set some test data
3. Simulate a Redis node failure by stopping one of the Redis containers
4. Continue making requests to see how Predixy handles the failure
5. Restart the failed Redis node
6. Observe recovery behavior
"""

import redis
import time
import subprocess
import argparse
import sys
import random


class FailureTest:
    def __init__(self, host="localhost", port=7617):
        """Initialize the failure test with connection to Predixy."""
        self.host = host
        self.port = port
        self.client = self._connect()
        self.test_keys = []

    def _connect(self):
        """Connect to Redis via Predixy proxy."""
        try:
            client = redis.Redis(
                host=self.host,
                port=self.port,
                db=0,
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

    def _run_command(self, cmd):
        """Run a shell command and return the output."""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e}")
            print(f"Error output: {e.stderr}")
            return None

    def setup_test_data(self, num_keys=100):
        """Set up test data before simulating failures."""
        print(f"Setting up {num_keys} test keys...")

        for i in range(num_keys):
            key = f"failure:test:key:{i}"
            value = f"test-value-{i}"

            success = self.client.set(key, value)
            if success:
                self.test_keys.append(key)

        print(f"Successfully set {len(self.test_keys)} test keys")

    def verify_data(self):
        """Verify that test data can be retrieved."""
        print("Verifying test data...")

        success_count = 0
        for key in self.test_keys:
            value = self.client.get(key)
            if value:
                success_count += 1

        print(f"Successfully retrieved {success_count}/{len(self.test_keys)} keys")
        return success_count

    def stop_redis_node(self, node_number):
        """Stop a Redis node to simulate failure."""
        container_name = f"redis{node_number}"
        print(f"Stopping Redis node {container_name}...")

        cmd = f"docker stop {container_name}"
        output = self._run_command(cmd)

        if output:
            print(f"Successfully stopped {container_name}")
            return True
        return False

    def start_redis_node(self, node_number):
        """Start a previously stopped Redis node."""
        container_name = f"redis{node_number}"
        print(f"Starting Redis node {container_name}...")

        cmd = f"docker start {container_name}"
        output = self._run_command(cmd)

        if output:
            print(f"Successfully started {container_name}")
            return True
        return False

    def run_continuous_operations(self, duration=30, interval=0.5):
        """Run continuous operations for a specified duration."""
        print(f"Running continuous operations for {duration} seconds...")

        end_time = time.time() + duration
        operations = 0
        errors = 0

        while time.time() < end_time:
            try:
                # Randomly choose between read and write operations
                op_type = random.choice(["read", "write"])

                if op_type == "read":
                    # Read a random test key
                    if self.test_keys:
                        key = random.choice(self.test_keys)
                        value = self.client.get(key)
                        if value:
                            operations += 1
                        else:
                            errors += 1
                else:
                    # Write a new key
                    key = f"failure:test:new:{random.randint(1, 10000)}"
                    value = f"new-value-{random.randint(1, 10000)}"
                    success = self.client.set(key, value)
                    if success:
                        operations += 1
                    else:
                        errors += 1

            except redis.RedisError as e:
                print(f"Redis error: {e}")
                errors += 1

            time.sleep(interval)

        print(f"Completed {operations} successful operations with {errors} errors")
        return operations, errors

    def run_failure_test(self, node_to_fail=2, operation_duration=30):
        """Run a complete failure test scenario."""
        # 1. Set up test data
        self.setup_test_data()

        # 2. Verify data can be retrieved
        initial_success = self.verify_data()

        # 3. Run operations for a while to establish baseline
        print("\n=== Running baseline operations ===")
        baseline_ops, baseline_errors = self.run_continuous_operations(duration=10)

        # 4. Stop a Redis node
        print("\n=== Simulating node failure ===")
        self.stop_redis_node(node_to_fail)

        # 5. Wait a moment for Predixy to detect the failure
        time.sleep(2)

        # 6. Run operations during failure
        print("\n=== Running operations during failure ===")
        failure_ops, failure_errors = self.run_continuous_operations(
            duration=operation_duration
        )

        # 7. Verify data during failure
        failure_success = self.verify_data()

        # 8. Restart the Redis node
        print("\n=== Recovering from failure ===")
        self.start_redis_node(node_to_fail)

        # 9. Wait for recovery
        time.sleep(5)

        # 10. Run operations during recovery
        print("\n=== Running operations during recovery ===")
        recovery_ops, recovery_errors = self.run_continuous_operations(duration=10)

        # 11. Final verification
        final_success = self.verify_data()

        # 12. Print summary
        print("\n=== Failure Test Summary ===")
        print(
            f"Initial data verification: {initial_success}/{len(self.test_keys)} keys"
        )
        print(
            f"Baseline operations: {baseline_ops} successful, {baseline_errors} errors"
        )
        print(
            f"Operations during failure: {failure_ops} successful, {failure_errors} errors"
        )
        print(
            f"Data verification during failure: {failure_success}/{len(self.test_keys)} keys"
        )
        print(
            f"Operations during recovery: {recovery_ops} successful, {recovery_errors} errors"
        )
        print(f"Final data verification: {final_success}/{len(self.test_keys)} keys")


def main():
    parser = argparse.ArgumentParser(description="Redis Failure Test")
    parser.add_argument("--host", default="localhost", help="Predixy host")
    parser.add_argument("--port", type=int, default=7617, help="Predixy port")
    parser.add_argument(
        "--node", type=int, default=3, help="Redis node to fail (1, 2, 3, or 4)"
    )
    parser.add_argument(
        "--duration", type=int, default=30, help="Duration of failure test in seconds"
    )
    parser.add_argument(
        "--node-type",
        choices=["master", "slave", "any"],
        default="any",
        help="Type of node to fail (master, slave, or any)",
    )

    args = parser.parse_args()

    if args.node not in [1, 2, 3, 4]:
        print("Node must be 1, 2, 3, or 4")
        sys.exit(1)

    # In our setup:
    # - Nodes 1 and 2 are masters
    # - Nodes 3 and 4 are slaves
    if args.node_type == "master" and args.node > 2:
        print(
            "Nodes 1 and 2 are masters. Please select node 1 or 2 for master failure test."
        )
        sys.exit(1)
    elif args.node_type == "slave" and args.node < 3:
        print(
            "Nodes 3 and 4 are slaves. Please select node 3 or 4 for slave failure test."
        )
        sys.exit(1)

    test = FailureTest(host=args.host, port=args.port)
    test.run_failure_test(node_to_fail=args.node, operation_duration=args.duration)


if __name__ == "__main__":
    main()
