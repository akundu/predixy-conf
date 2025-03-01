# Redis Cluster with Predixy Proxy

This project sets up a Redis cluster with 4 servers (2 masters and 2 slaves) and a Predixy proxy in front of it. It also includes a Python client to connect to the proxy and test how Predixy handles server errors and failures.

## Components

- **Redis Cluster**: 4 Redis servers configured as a cluster (2 masters, 2 slaves)
- **Predixy Proxy**: A high-performance Redis proxy that sits in front of the Redis cluster
- **Python Client**: A client that connects to the Predixy proxy to make Redis requests
- **Failure Testing**: Scripts to test how Predixy handles server errors and failures

## Setup Instructions

### Prerequisites

- Docker and Docker Compose
- Python 3.6+
- pip (Python package manager)

### Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Start the Redis cluster and Predixy proxy:
   ```
   docker-compose up -d
   ```

4. Initialize the Redis cluster:
   ```
   ./init-cluster.sh
   ```

### Usage

#### Basic Redis Client

The `redis_client.py` script provides a basic client to interact with Redis through the Predixy proxy:

```
python redis_client.py --ops 100
```

Options:
- `--host`: Predixy host (default: localhost)
- `--port`: Predixy port (default: 7617)
- `--ops`: Number of operations to run (default: 100)
- `--test-errors`: Test error handling
- `--high-load`: Simulate high load
- `--load-duration`: Duration of high load test in seconds (default: 10)
- `--threads`: Number of threads for high load test (default: 5)

#### Failure Testing

The `test_failures.py` script simulates Redis node failures and tests how Predixy handles them:

```
python test_failures.py --node 3 --node-type slave --duration 30
```

Options:
- `--host`: Predixy host (default: localhost)
- `--port`: Predixy port (default: 7617)
- `--node`: Redis node to fail (1, 2, 3, or 4) (default: 3)
- `--node-type`: Type of node to fail (master, slave, or any) (default: any)
- `--duration`: Duration of failure test in seconds (default: 30)

Note: In our setup, nodes 1 and 2 are masters, while nodes 3 and 4 are slaves.

## Configuration Files

### Redis Configuration

Each Redis node has its own configuration file:
- `redis/redis1.conf`
- `redis/redis2.conf`
- `redis/redis3.conf`

### Predixy Configuration

Predixy configuration files:
- `predixy/conf/predixy.conf`: Main configuration file
- `predixy/conf/cluster.conf`: Redis cluster configuration
- `predixy/conf/latency.conf`: Latency monitoring configuration
- `predixy/conf/read.conf`: Read strategy configuration

## Testing Scenarios

1. **Basic Operations**: Test basic Redis operations through the Predixy proxy
   ```
   python redis_client.py
   ```

2. **Error Handling**: Test how Predixy handles Redis errors
   ```
   python redis_client.py --test-errors
   ```

3. **High Load**: Test Predixy under high load
   ```
   python redis_client.py --high-load --threads 10 --load-duration 30
   ```

4. **Node Failure**: Test how Predixy handles Redis node failures
   ```
   python test_failures.py --node 3 --node-type slave --duration 30
   ```

## Cleanup

To stop and remove all containers:
```
docker-compose down
```

## Troubleshooting

- If the Redis cluster initialization fails, make sure all Redis nodes are running:
  ```
  docker ps | grep redis
  ```

- If you can't connect to Predixy, check if it's running:
  ```
  docker ps | grep predixy
  ```

- To view logs:
  ```
  docker logs redis1
  docker logs redis2
  docker logs redis3
  docker logs predixy
  ``` 