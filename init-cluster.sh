#!/bin/bash

# Wait for Redis nodes to be ready
echo "Waiting for Redis nodes to start..."
sleep 5

# Create Redis cluster with 2 masters and 2 slaves
echo "Creating Redis cluster with 2 masters and 2 slaves..."
docker exec -it redis1 redis-cli --cluster create \
    redis1:6379 \
    redis2:6379 \
    redis3:6379 \
    redis4:6379 \
    --cluster-replicas 1 --cluster-yes

# The --cluster-replicas 1 option means for every master, create 1 replica (slave)
# This will automatically assign redis3 and redis4 as slaves to redis1 and redis2

echo "Redis cluster created successfully!"
echo "You can now use the Predixy proxy at localhost:7617"

docker-compose up -d 